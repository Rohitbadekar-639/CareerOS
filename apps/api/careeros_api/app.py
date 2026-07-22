from fastapi import FastAPI

from careeros_api.errors import register_exception_handlers
from careeros_api.health import health_router
from careeros_api.router import api_router
from careeros_platform.settings import Settings, get_settings
from careeros_platform.tracing import RequestIdMiddleware, configure_tracing


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings if settings is not None else get_settings()
    configure_tracing(resolved.app_name)
    app = FastAPI(title=resolved.app_name)
    app.state.settings = resolved
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    return app
