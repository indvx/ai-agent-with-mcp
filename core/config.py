from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # LLM settings
    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-20b"
    llm_base_url: Optional[str] = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_temperature: float = 0.3

    # MCP settings
    mcp_url: str = "http://localhost:8001/mcp"

    # Logging settings
    log_level: str = "INFO"

    # Cache settings
    cache_ttl_seconds: int = 300
    cache_max_size: int = 500

    # CORS settings
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
