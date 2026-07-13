from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from app.core.github_webhook import validate_signature
from app.config.settings import settings
from app.core.logger import logger
from app.services.pull_request import process_pull_request
from app.schemas.github import GitHubWebhookPayload
from app.cache.redis_client import redis_client
import json

router = APIRouter()

@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_delivery: str = Header(None)
):
    if not x_hub_signature_256:
        logger.warning("Webhook received without signature")
        raise HTTPException(status_code=400, detail="Signature missing")

    if not x_github_delivery:
        logger.warning("Webhook received without delivery ID")
        raise HTTPException(status_code=400, detail="Delivery ID missing")

    # 1. Deduplication Check
    is_duplicate = await redis_client.is_duplicate_delivery(x_github_delivery)
    if is_duplicate:
        logger.info(f"Ignored duplicate webhook delivery: {x_github_delivery}")
        return {"status": "ignored", "reason": "duplicate delivery"}

    # Read the raw body
    payload = await request.body()
    
    # Validate Signature
    is_valid = validate_signature(payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET)
    if not is_valid:
        logger.warning("Webhook signature validation failed")
        raise HTTPException(status_code=403, detail="Invalid signature")
        
    logger.info("Webhook signature validated successfully")
    
    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    event = request.headers.get("X-GitHub-Event", "")
    
    # Ignore unsupported events
    if event != "pull_request":
        logger.info(f"Ignoring unsupported GitHub event: {event}")
        return {"status": "ignored", "reason": "unsupported event"}
        
    # We only care about opened, synchronize, and reopened actions
    action = data.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        logger.info(f"Ignoring pull_request action: {action}")
        return {"status": "ignored", "reason": "unsupported action"}
        
    try:
        webhook_payload = GitHubWebhookPayload(**data)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload structure")
        
    owner = webhook_payload.repository.owner.login
    repo = webhook_payload.repository.name
    pr_number = webhook_payload.pull_request.number
    sender = webhook_payload.sender.login
    
    logger.info(f"Received valid PR event ({action}) from {sender} for {owner}/{repo}#{pr_number}")
    
    # Register PR state
    await redis_client.set_pr_status(repo, pr_number, "QUEUED")
    
    # Queue background task
    background_tasks.add_task(process_pull_request, owner, repo, pr_number)
    
    return {"status": "accepted"}
