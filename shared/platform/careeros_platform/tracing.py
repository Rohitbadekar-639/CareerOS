"""Tracing + request correlation (T11).

Provides an OpenTelemetry skeleton (a global ``TracerProvider`` with service
identity, no exporter yet), a request-scoped correlation id stored in a
``ContextVar``, a logging filter that stamps every log line with that id, and a
framework-free ASGI middleware that opens a span per request, exposes its trace
id on the response, and makes it available to the log filter.

Kept free of any web-framework import so the shared platform stays vendor-neutral.
"""

import logging
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

TRACE_ID_HEADER = "x-trace-id"

trace_id_var: ContextVar[str | None] = ContextVar("careeros_trace_id", default=None)

_configured = False


def configure_tracing(service_name: str) -> None:
    """Install a global ``TracerProvider`` once (idempotent).

    No span exporter is wired yet — this is the plumbing that lets spans carry a
    real trace id and lets exporters be added later without touching callers.
    """
    global _configured
    if _configured:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    _configured = True


def get_current_trace_id() -> str | None:
    return trace_id_var.get()


class TraceIdLogFilter(logging.Filter):
    """Stamp each record with the current request's trace id (if any)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        return True


# Minimal ASGI typing so the platform stays framework-agnostic.
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class RequestIdMiddleware:
    """ASGI middleware that opens a span per HTTP request and propagates its
    trace id into the context var, the logs, and the response header."""

    def __init__(self, app: ASGIApp, *, header_name: str = TRACE_ID_HEADER) -> None:
        self._app = app
        self._header = header_name.lower().encode("latin-1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        tracer = trace.get_tracer("careeros.platform")
        with tracer.start_as_current_span("http.request") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            token = trace_id_var.set(trace_id)
            header_value = trace_id.encode("latin-1")

            async def send_with_trace(message: Message) -> None:
                if message["type"] == "http.response.start":
                    headers = message.setdefault("headers", [])
                    headers.append((self._header, header_value))
                await send(message)

            try:
                await self._app(scope, receive, send_with_trace)
            finally:
                trace_id_var.reset(token)
