"""Configuration management for the Solana Wallet Tracker.

This module defines the Settings class that loads environment variables
from a .env file and provides validated configuration for the application.
"""

from __future__ import annotations

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram Settings
    bot_token: str
    admin_id: int

    # Database Settings
    db_path: str = "data/bot.db"

    @computed_field
    @property
    def db_url(self) -> str:
        """Returns the SQLAlchemy connection string."""
        return f"sqlite+aiosqlite:///{self.db_path}"

    # Helius Settings
    helius_api_key: str
    source_webhook_id: str
    tracked_webhook_id: str

    @computed_field
    @property
    def helius_rpc_url(self) -> str:
        """Returns the Helius RPC endpoint with API key."""
        return f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"

    # Logic Defaults
    default_min_sol: float = 0.1
    default_max_sol: float = 100.0
    timezone_offset: int = 0

    # Server Settings
    server_host: str = "0.0.0.0"
    server_port: int = 8000


settings = Settings()
