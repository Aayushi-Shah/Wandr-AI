from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://wandr:wandr@localhost:5432/wandr"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Anthropic
    anthropic_api_key: str = ""

    # JWT
    jwt_secret_key: str = "change-me-must-be-at-least-32-characters-long"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # MCP server URLs
    mcp_web_search_url: str = "https://search.mcp.anthropic.com"
    mcp_maps_url: str = "https://maps.mcp.anthropic.com"
    mcp_weather_url: str = "https://weather.mcp.anthropic.com"
    mcp_currency_url: str = "https://currency.mcp.anthropic.com"
    mcp_calendar_url: str = "https://gcal.mcp.claude.com/mcp"

    # Feature flags
    enable_calendar_mcp: bool = False

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "wandr-backend"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
