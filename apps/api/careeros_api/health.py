"""Liveness and readiness endpoints (T12).

Thin transport over the shared platform health primitives. Readiness will grow
real dependency probes (database, queue) once those adapters land.
"""

from fastapi import APIRouter

from careeros_platform.health import liveness, readiness

health_router = APIRouter(tags=["health"])


@health_router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": liveness().status.value}


@health_router.get("/readyz")
def readyz() -> dict[str, object]:
    report = readiness()
    return {
        "status": report.status.value,
        "checks": {name: status.value for name, status in report.checks.items()},
    }
