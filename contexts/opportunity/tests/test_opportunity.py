"""Unit tests for Opportunity value objects + ingest dedup."""

from careeros_opportunity.domain.opportunity import Opportunity
from careeros_opportunity.domain.value_objects import (
    CompanyName,
    DedupKey,
    SourceKind,
    SourceProvenance,
)


def test_dedup_key_stable() -> None:
    a = DedupKey.from_parts(
        company="Stripe",
        title="Software Engineer",
        location="Remote",
        apply_url="https://example.com/jobs/1",
    )
    b = DedupKey.from_parts(
        company="stripe",
        title="Software  Engineer",
        location="remote",
        apply_url="https://example.com/jobs/1",
    )
    assert str(a) == str(b)


def test_opportunity_ingest_emits_activated() -> None:
    opp = Opportunity.ingest_normalized(
        title="Backend Engineer",
        company=CompanyName("Acme"),
        location="Bengaluru",
        is_remote=False,
        description_text="Python FastAPI",
        apply_url="https://example.com/j/1",
        provenance=SourceProvenance(
            kind=SourceKind.GREENHOUSE,
            board_token="acme",
            external_id="1",
            source_url="https://example.com/j/1",
        ),
        skills=["python", "fastapi"],
    )
    events = opp.pull_events()
    assert len(events) == 1
    assert opp.status.value == "active"
