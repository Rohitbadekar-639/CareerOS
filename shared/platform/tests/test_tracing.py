import io
import json
import logging

from careeros_platform.logging import configure_logging, get_logger
from careeros_platform.tracing import (
    TraceIdLogFilter,
    configure_tracing,
    get_current_trace_id,
    trace_id_var,
)


def test_configure_tracing_is_idempotent() -> None:
    configure_tracing("careeros-test")
    configure_tracing("careeros-test")


def test_trace_id_defaults_to_none_outside_request() -> None:
    assert get_current_trace_id() is None


def test_trace_id_log_filter_injects_current_id() -> None:
    token = trace_id_var.set("abc123")
    try:
        record = logging.LogRecord("t", logging.INFO, "", 0, "msg", None, None)
        assert TraceIdLogFilter().filter(record) is True
        assert record.trace_id == "abc123"  # type: ignore[attr-defined]
    finally:
        trace_id_var.reset(token)


def test_trace_id_appears_in_log_output() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer, filters=[TraceIdLogFilter()])
    token = trace_id_var.set("trace-xyz")
    try:
        get_logger("careeros.test").info("hi")
    finally:
        trace_id_var.reset(token)

    record = json.loads(buffer.getvalue().strip().splitlines()[-1])
    assert record["trace_id"] == "trace-xyz"
