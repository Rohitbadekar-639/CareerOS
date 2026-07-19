from careeros_platform.health import HealthStatus, liveness, readiness


def test_liveness_is_ok() -> None:
    assert liveness().status is HealthStatus.OK


def test_readiness_defaults_to_ok_self_check() -> None:
    report = readiness()
    assert report.status is HealthStatus.OK
    assert report.checks == {"self": HealthStatus.OK}


def test_readiness_is_degraded_when_a_check_fails() -> None:
    report = readiness({"database": HealthStatus.OK, "queue": HealthStatus.DEGRADED})
    assert report.status is HealthStatus.DEGRADED


def test_readiness_is_ok_when_all_checks_pass() -> None:
    report = readiness({"database": HealthStatus.OK, "queue": HealthStatus.OK})
    assert report.status is HealthStatus.OK
