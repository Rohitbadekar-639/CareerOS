from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from careeros_shared_kernel.events import DomainEvent


def test_base_event_has_identity_and_timestamp() -> None:
    event = DomainEvent()
    assert isinstance(event.event_id, UUID)
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo is UTC
    assert event.event_version == 1


def test_events_get_distinct_ids() -> None:
    assert DomainEvent().event_id != DomainEvent().event_id


def test_event_is_immutable() -> None:
    event = DomainEvent()
    with pytest.raises(AttributeError):
        event.event_version = 2  # type: ignore[misc]


def test_subclass_adds_payload_fields() -> None:
    @dataclass(frozen=True, slots=True, kw_only=True)
    class CandidateRegistered(DomainEvent):
        candidate_id: str

    event = CandidateRegistered(candidate_id="cand-1")
    assert event.candidate_id == "cand-1"
    assert event.event_version == 1
