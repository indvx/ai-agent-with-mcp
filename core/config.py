from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal

class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # Database connection settings
    db_connection: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_ssl_mode: Literal["require", "disable"]
    db_ssl_key: Optional[str] = None

    # LLM settings
    llm_provider: str
    llm_model : str
    llm_base_url : str
    llm_api_key : str
    llm_temperature : str

    # MCP settings
    mcp_url : str

    # Auth settings
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore", 
    )


# Singleton instance reused across the app
settings = Settings()
