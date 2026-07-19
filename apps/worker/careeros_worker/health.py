"""Worker health check (T12).

The worker is an async job runtime, not an HTTP service, so its liveness/
readiness surface is a CLI (``python -m careeros_worker.health``) suitable for a
container ``HEALTHCHECK``: exit 0 when ready, non-zero otherwise. Dependency
probes are stubbed until their adapters exist.
"""

from careeros_platform.health import HealthReport, HealthStatus, liveness, readiness


def check_liveness() -> HealthReport:
    return liveness()


def check_readiness() -> HealthReport:
    return readiness()


def main() -> int:
    report = check_readiness()
    return 0 if report.status is HealthStatus.OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
