"""Configuration management with Pydantic.

Type-safe, validated configuration from environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.constants import FilePath, ModelConfig


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=FilePath.ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required
    openrouter_api_key: SecretStr = Field(
        ...,
        description="OpenRouter API key for LLM access",
    )

    # Optional with defaults
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Model selection
    default_model: str = Field(
        default=ModelConfig.DEFAULT_CHAT_MODEL,
        description="Default chat model",
    )

    heart_model: str = Field(
        default=ModelConfig.DEFAULT_HEART_MODEL,
        description="Fast model for preview/analysis",
    )

    instant_preview: bool = Field(
        default=False,
        description="Enable instant preview feature",
    )

    # Memory
    memory_backend: str = Field(
        default="sqlite",
        description="Memory storage backend",
    )

    # Database
    database_url: str = Field(
        default=f"sqlite:///{FilePath.DB_FILE}",
        description="Database connection URL",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate API key format."""
        key = v.get_secret_value()
        if not key.startswith("sk-or-v1-"):
            raise ValueError("API key must start with 'sk-or-v1-'")
        if len(key) < 20:
            raise ValueError("API key too short")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export for convenient access
settings = get_settings()
