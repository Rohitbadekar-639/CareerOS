import uvicorn

from careeros_platform.logging import configure_logging
from careeros_platform.settings import get_settings
from careeros_platform.tracing import TraceIdLogFilter, configure_tracing


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, filters=[TraceIdLogFilter()])
    configure_tracing(settings.app_name)
    uvicorn.run(
        "careeros_api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    main()
