"""Structured JSON logging (T10).

A ``logging.Formatter`` that emits one JSON object per line, plus key-based
PII/secret redaction of structured ``extra`` fields. Log level comes from
configuration. Trace-id enrichment is layered on separately (T11) via a logging
filter, keeping this module free of any tracing dependency.
"""

import json
import logging
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, TextIO

REDACTED = "***redacted***"

# Structured keys whose values are secrets or PII and must never be logged.
DEFAULT_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "authorization",
        "database_url",
        "email",
        "phone",
    }
)

# Standard ``LogRecord`` attributes; anything else is treated as a structured extra.
_RESERVED_RECORD_KEYS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
        "trace_id",
    }
)


def redact_mapping(data: Mapping[str, Any], sensitive_keys: frozenset[str]) -> dict[str, Any]:
    """Return a copy with sensitive keys masked, recursing into nested mappings."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            result[key] = REDACTED
        elif isinstance(value, Mapping):
            result[key] = redact_mapping(value, sensitive_keys)
        else:
            result[key] = value
    return result


class JsonFormatter(logging.Formatter):
    def __init__(self, sensitive_keys: frozenset[str] = DEFAULT_SENSITIVE_KEYS) -> None:
        super().__init__()
        self._sensitive_keys = sensitive_keys

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        trace_id = getattr(record, "trace_id", None)
        if trace_id:
            payload["trace_id"] = trace_id

        extras = {
            key: value for key, value in record.__dict__.items() if key not in _RESERVED_RECORD_KEYS
        }
        if extras:
            payload["context"] = redact_mapping(extras, self._sensitive_keys)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(
    level: str = "INFO",
    *,
    stream: TextIO | None = None,
    filters: Sequence[logging.Filter] | None = None,
    sensitive_keys: frozenset[str] = DEFAULT_SENSITIVE_KEYS,
) -> None:
    """Configure the root logger with a single JSON handler.

    Idempotent: existing handlers are replaced so repeated calls (e.g. api and
    worker entrypoints) do not duplicate output.
    """
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(JsonFormatter(sensitive_keys=sensitive_keys))
    for log_filter in filters or ():
        handler.addFilter(log_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
