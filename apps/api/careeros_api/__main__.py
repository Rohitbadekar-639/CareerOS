import uvicorn

from careeros_platform.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "careeros_api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    main()
