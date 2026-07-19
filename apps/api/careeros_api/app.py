from fastapi import FastAPI

from careeros_api.router import api_router
from careeros_platform.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings if settings is not None else get_settings()
    app = FastAPI(title=resolved.app_name)
    app.include_router(api_router)
    return app
