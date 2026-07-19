from careeros_platform.health import HealthStatus
from careeros_worker.health import check_liveness, check_readiness, main


def test_worker_liveness_is_ok() -> None:
    assert check_liveness().status is HealthStatus.OK


def test_worker_readiness_is_ok() -> None:
    assert check_readiness().status is HealthStatus.OK


def test_health_cli_exits_zero_when_ready() -> None:
    assert main() == 0
