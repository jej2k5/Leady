"""Typed application configuration loaded from environment variables and .env files."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseModel):
    app_name: str = "leadbot"
    environment: str = "dev"
    log_level: str = "INFO"
    log_file: str = "logs/leady-api.log"


class ApiSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"


class AuthSettings(BaseModel):
    provider: str = "authy"
    jwt_secret: str = "change-me-in-production-minimum-32-chars"
    jwt_ttl_seconds: int = 3600
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"


class ScrapingSettings(BaseModel):
    user_agent: str = "leadbot/0.1"
    timeout_seconds: int = 20
    max_retries: int = 2


class DiscoverySettings(BaseModel):
    batch_size: int = 25
    max_candidates_per_run: int = 500
    auto_start_enabled: bool = False
    auto_start_hour_utc: int = 3
    auto_start_days: int = 30
    auto_start_sources: str = "funding,hiring,github"
    auto_start_max_candidates: int = 25
    auto_start_categories: list[str] = Field(default_factory=list)


class ScoringSettings(BaseModel):
    default_threshold: float = 0.5
    max_score: float = 100.0


class McpSettings(BaseModel):
    enabled: bool = False
    transport: str = "stdio"
    endpoint: str = ""


class SheetsSettings(BaseModel):
    enabled: bool = False
    spreadsheet_id: str = ""
    worksheet_name: str = "Leads"


class Settings(BaseSettings):
    """Runtime settings grouped by functional area."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    core: CoreSettings = Field(default_factory=CoreSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    discovery: DiscoverySettings = Field(default_factory=DiscoverySettings)
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    mcp: McpSettings = Field(default_factory=McpSettings)
    sheets: SheetsSettings = Field(default_factory=SheetsSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings."""
    return Settings()
