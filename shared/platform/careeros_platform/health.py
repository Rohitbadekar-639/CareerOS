"""Health primitives (T12).

Shared, transport-agnostic liveness/readiness reporting used by both the api
(HTTP endpoints) and the worker (health CLI). Dependency probes (database,
queue, ...) are stubbed until their adapters exist; readiness accepts a map of
named check results so real probes can be wired later without changing callers.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class HealthReport:
    status: HealthStatus
    checks: Mapping[str, HealthStatus] = field(default_factory=dict)


def liveness() -> HealthReport:
    """Process is up and able to respond."""
    return HealthReport(status=HealthStatus.OK)


def readiness(checks: Mapping[str, HealthStatus] | None = None) -> HealthReport:
    """Aggregate dependency checks into an overall readiness verdict.

    With no checks supplied, reports readiness of the process itself. Overall
    status is degraded if any individual check is not OK.
    """
    resolved: dict[str, HealthStatus] = (
        dict(checks) if checks is not None else {"self": HealthStatus.OK}
    )
    overall = (
        HealthStatus.OK
        if all(status is HealthStatus.OK for status in resolved.values())
        else HealthStatus.DEGRADED
    )
    return HealthReport(status=overall, checks=resolved)
