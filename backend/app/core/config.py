from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CyberSec Platform"
    APP_ENV: str = "development"  # development | production
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-2b93c0bde6aa7792ed00098166c55bdb"
    
    # Database (defaults to local sqlite for seamless execution without postgres)
    DATABASE_URL: str = "sqlite+aiosqlite:///./cybersec.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "dev-jwt-secret-cf7271eaa3a00e81215d3218556a6159"
    JWT_REFRESH_SECRET_KEY: str = "dev-jwt-refresh-1e6ee27951247a2568e0df6c29992"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # AI
    AI_PROVIDER: str = "openai"  # openai | anthropic
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Scanner
    SCANNER_REQUEST_TIMEOUT: int = 30
    SCANNER_MAX_REDIRECTS: int = 5
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
