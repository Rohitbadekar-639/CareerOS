"""Problem-details error mapping (T12, RFC 9457).

Maps expected domain errors to safe HTTP problem+json responses and converts any
unexpected exception into a generic 500 problem-detail — never leaking stack
traces or internal messages. The trace id is attached when available so a client
error can be correlated to server logs.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from careeros_platform.logging import get_logger
from careeros_platform.tracing import get_current_trace_id
from careeros_shared_kernel.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

PROBLEM_CONTENT_TYPE = "application/problem+json"

_logger = get_logger("careeros.api.errors")

# Domain error -> HTTP status. Base DomainError falls back to 400.
_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (ValidationError, 422),
    (NotFoundError, 404),
    (ConflictError, 409),
    (PermissionDeniedError, 403),
)


def _problem(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    trace_id = get_current_trace_id()
    if trace_id:
        body["trace_id"] = trace_id
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_CONTENT_TYPE)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status = next(
        (code for error_type, code in _STATUS_BY_ERROR if isinstance(exc, error_type)),
        400,
    )
    detail = str(exc) or exc.__class__.__name__
    return _problem(status, exc.__class__.__name__, detail, request.url.path)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _logger.error(
        "unhandled_exception",
        extra={"path": request.url.path, "error_type": exc.__class__.__name__},
    )
    return _problem(
        500,
        "Internal Server Error",
        "An unexpected error occurred.",
        request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
