import io
import json

from fastapi.testclient import TestClient

from careeros_api.app import create_app
from careeros_platform.logging import configure_logging, get_logger
from careeros_platform.settings import Environment, Settings
from careeros_platform.tracing import TRACE_ID_HEADER, TraceIdLogFilter


def _test_settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost:5432/careeros_test",
        environment=Environment.DEVELOPMENT,
    )


def test_request_and_log_share_a_trace_id() -> None:
    buffer = io.StringIO()
    configure_logging("INFO", stream=buffer, filters=[TraceIdLogFilter()])

    app = create_app(_test_settings())

    @app.get("/_probe")
    def _probe() -> dict[str, str]:
        get_logger("careeros.api.test").info("probe handled")
        return {"ok": "true"}

    with TestClient(app) as client:
        response = client.get("/_probe")

    assert response.status_code == 200
    header_trace_id = response.headers[TRACE_ID_HEADER]
    assert header_trace_id

    log_lines = [json.loads(line) for line in buffer.getvalue().strip().splitlines() if line]
    probe_logs = [entry for entry in log_lines if entry["message"] == "probe handled"]
    assert probe_logs, "expected the handler log line to be captured"
    assert probe_logs[0]["trace_id"] == header_trace_id
