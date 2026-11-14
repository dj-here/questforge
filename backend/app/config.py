import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pathlib import Path

def get_prompts_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[2] / "prompts" / "v1",
        Path(__file__).resolve().parents[1] / "prompts" / "v1",
        Path("prompts/v1"),
        Path("/prompts/v1")
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return candidates[0]

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "QuestForge"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "questforge-super-secret-jwt-key-change-in-production-32bytes-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    POSTGRES_URL: Optional[str] = None
    NEON_DATABASE_URL: Optional[str] = None
    QUESTFORGE_DATABASE_URL: Optional[str] = None
    DATABASE_URL: str = "sqlite:///./questforge.db"

    @property
    def effective_db_url(self) -> str:
        if self.QUESTFORGE_DATABASE_URL:
            return self.QUESTFORGE_DATABASE_URL
        if self.POSTGRES_URL:
            return self.POSTGRES_URL
        if os.environ.get("USE_NEON", "").lower() in ("true", "1") and (self.NEON_DATABASE_URL or self.DATABASE_URL):
            return self.NEON_DATABASE_URL or self.DATABASE_URL
        if self.ENVIRONMENT == "production" and self.DATABASE_URL and not self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL
        if "neondb" in self.DATABASE_URL and os.environ.get("USE_NEON", "").lower() not in ("true", "1"):
            return "sqlite:///./questforge.db"
        return self.DATABASE_URL
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # LLM Settings (Supports Google Gemini & Anthropic Claude)
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    ANTHROPIC_API_KEY: str = "mock-anthropic-key"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    MOCK_LLM: bool = False
    
    # Sandbox
    SANDBOX_TYPE: str = "subprocess"  # "docker", "subprocess", "mock"
    SANDBOX_TIMEOUT_SECONDS: int = 8
    SANDBOX_MEMORY_LIMIT_MB: int = 256
    
    # HackerRank
    HACKERRANK_API_TOKEN: str = "mock-hr-token"
    HACKERRANK_BASE_URL: str = "https://www.hackerrank.com/x/api/v3"
    HACKERRANK_DRY_RUN: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Pipeline
    MAX_REGENERATE_ATTEMPTS: int = 3
    CRITIC_MIN_SCORE: float = 7.0
    DEDUP_SIMILARITY_THRESHOLD: float = 0.85

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
