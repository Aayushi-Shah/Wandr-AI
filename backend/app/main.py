from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.v1.router import v1_router
from app.core.config import Settings, get_settings
from app.core.database import close_db, init_db
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings
    await init_db(settings.database_url)
    await init_redis(settings.redis_url)
    logger.info("wandr-backend started", env=settings.otel_service_name)
    yield
    await close_db()
    await close_redis()
    logger.info("wandr-backend stopped")


def create_app() -> FastAPI:
    configure_logging()
    settings: Settings = get_settings()

    app = FastAPI(
        title="wandr-ai API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.include_router(v1_router, prefix="/api/v1")

    return app
