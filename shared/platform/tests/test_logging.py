import io
import json
import logging

from careeros_platform.logging import (
    REDACTED,
    configure_logging,
    get_logger,
)


def _read_json_line(buffer: io.StringIO) -> dict[str, object]:
    line = buffer.getvalue().strip().splitlines()[-1]
    record: dict[str, object] = json.loads(line)
    return record


def test_log_output_is_structured_json() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer)
    get_logger("careeros.test").info("service started")

    record = _read_json_line(buffer)
    assert record["level"] == "INFO"
    assert record["logger"] == "careeros.test"
    assert record["message"] == "service started"
    assert isinstance(record["timestamp"], str)


def test_sensitive_extra_fields_are_redacted() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer)
    get_logger("careeros.test").info(
        "auth attempt",
        extra={"password": "hunter2", "user_id": "u-1"},
    )

    record = _read_json_line(buffer)
    context = record["context"]
    assert isinstance(context, dict)
    assert context["password"] == REDACTED
    assert context["user_id"] == "u-1"


def test_nested_sensitive_fields_are_redacted() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer)
    get_logger("careeros.test").info("payload", extra={"body": {"token": "abc", "keep": "yes"}})

    record = _read_json_line(buffer)
    body = record["context"]["body"]  # type: ignore[index]
    assert body["token"] == REDACTED
    assert body["keep"] == "yes"


def test_level_from_config_filters_lower_levels() -> None:
    buffer = io.StringIO()
    configure_logging("WARNING", stream=buffer)
    logger = get_logger("careeros.test")
    logger.info("should be dropped")
    logger.warning("should appear")

    lines = [line for line in buffer.getvalue().strip().splitlines() if line]
    assert len(lines) == 1
    assert json.loads(lines[0])["message"] == "should appear"


def test_configure_logging_is_idempotent() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer)
    configure_logging("INFO", stream=buffer)
    get_logger("careeros.test").info("once")

    lines = [line for line in buffer.getvalue().strip().splitlines() if line]
    assert len(lines) == 1


def test_get_logger_returns_standard_logger() -> None:
    assert isinstance(get_logger("careeros.test"), logging.Logger)
