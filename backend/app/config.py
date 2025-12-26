"""
Configuration Management

WHY: Centralized config prevents scattered environment variables.
In agentic systems, all agents need consistent settings (model, timeout, etc.)
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    WHY PYDANTIC SETTINGS:
    - Type validation (catches config errors at startup)
    - Default values (agents work even if .env is incomplete)
    - IDE autocomplete (reduces bugs)
    """
    
    # ==================== LLM Configuration ====================
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"  # Default model for all agents
    parsing_model: str = "llama-3.3-70b-versatile"
    scoring_model: str = "llama-3.3-70b-versatile"
    feedback_model: str = "llama-3.3-70b-versatile"
    ai_temperature: float = 0.1
    max_tokens: int = 8000
    
    # ==================== Application Settings ====================
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"
    
    # ==================== Database ====================
    database_url: str = ""  # Optional - uses in-memory if not set
    postgres_user: str = "resume_user"
    postgres_password: str = "resume_pass"
    postgres_db: str = "resume_screening"
    
    # ==================== Redis ====================
    redis_url: str = "redis://localhost:6379/0"
    
    # ==================== Security ====================
    api_key: str = ""  # Optional - no auth if empty
    secret_key: str = "change-this-in-production"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # ==================== Rate Limiting ====================
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # ==================== File Upload Settings ====================
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    max_batch_size: int = 20
    
    # ==================== Screening Thresholds ====================
    hire_threshold: float = 75.0
    reject_threshold: float = 50.0
    
    # ==================== Docker Settings ====================
    workers: int = 4
    
    # ==================== Monitoring ====================
    sentry_dsn: str = ""
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def use_database(self) -> bool:
        """Check if database is configured."""
        return bool(self.database_url)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached settings instance.
    
    WHY @lru_cache:
    - Settings are loaded once, not on every request
    - Agents share the same config instance
    - Faster API responses
    """
    return Settings()


# Module-level settings instance for convenient imports
# Usage: from app.config import settings
settings = get_settings()
