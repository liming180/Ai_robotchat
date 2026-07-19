"""
Configuration management for the AI Companion application.
Uses Pydantic Settings for type-safe configuration.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings with type validation.
    Loads from environment variables or .env file.
    """

    # Application
    app_name: str = "AI_Companion"
    app_env: str = "development"
    app_port: int = 8000
    app_debug: bool = True

    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 7

    # GLM API
    glm_api_key: str
    glm_api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    glm_model: str = "GLM-4.5-Air"

    # CORS
    cors_origins: str

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()
