import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.auth import create_access_token, create_refresh_token, verify_password
from app.db.database import get_db
from app.db.models import User

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.username, role=user.role.name)
    refresh_token = create_refresh_token(subject=user.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user.role.name,
    }


@router.get("/demo-access")
async def demo_access():
    """Redirect to the dashboard with the demo flag.

    The /dashboard endpoint handles server-side token injection when
    the ?demo=1 parameter is present, eliminating all client-side race
    conditions.
    """
    return RedirectResponse(url="/dashboard?demo=1", status_code=302)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = jwt.decode(
            payload.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = data.get("sub")
        token_type: str = data.get("type")
        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(subject=user.username, role=user.role.name)
    return {"access_token": access_token}


@router.get("/google/login")
async def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")
    
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code&"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        "scope=openid%20email%20profile&"
        "access_type=offline"
    )
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            error_detail = "Failed to retrieve token from Google"
            try:
                err_json = response.json()
                if "error_description" in err_json:
                    error_detail = f"Google Error: {err_json['error_description']}"
                elif "error" in err_json:
                    error_detail = f"Google Error: {err_json['error']}"
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=error_detail)
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")
            
        user_info = user_info_response.json()

    # Look up user or create new
    google_id = user_info.get("id")
    email = user_info.get("email")
    picture = user_info.get("picture")
    
    result = await db.execute(select(User).where((User.google_id == google_id) | (User.username == email)))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            username=email,
            google_id=google_id,
            auth_provider="GOOGLE",
            avatar_url=picture,
            hashed_password=None
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.auth_provider == "LOCAL":
        # Link account
        user.google_id = google_id
        user.auth_provider = "GOOGLE"
        user.avatar_url = picture
        await db.commit()
        await db.refresh(user)
        
    prism_access_token = create_access_token(subject=user.username, role=user.role.name)
    
    html = f"""
    <html>
        <body>
            <script>
                localStorage.setItem('prism_token', '{prism_access_token}');
                window.location.href = '/dashboard';
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
