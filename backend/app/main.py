from fastapi import FastAPI

from app.api.v1.router import v1_router
from app.core.config import Settings, get_settings


def create_app() -> FastAPI:
    settings: Settings = get_settings()

    app = FastAPI(
        title="wandr-ai API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.state.settings = settings
    app.include_router(v1_router, prefix="/api/v1")

    return app
