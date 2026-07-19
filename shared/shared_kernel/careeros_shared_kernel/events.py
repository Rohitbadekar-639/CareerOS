"""Base domain-event type.

Domain events are immutable, past-tense facts. Concrete events subclass
``DomainEvent`` (keyword-only) and add their own payload fields. Cross-context
communication happens only through these events.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_version: int = 1
