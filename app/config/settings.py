from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReviewSense"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    GROQ_API_KEY: str
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    
    DATABASE_URL: str
    REDIS_URL: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
