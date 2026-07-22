"""Opportunity aggregate root."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from careeros_opportunity.domain.events import (
    DuplicateOpportunityCollapsed,
    OpportunityActivated,
)
from careeros_opportunity.domain.lifecycle import OpportunityStatus
from careeros_opportunity.domain.value_objects import (
    CompanyName,
    DedupKey,
    OpportunityId,
    SourceProvenance,
)
from careeros_shared_kernel import DomainEvent, ValidationError


@dataclass(frozen=True, slots=True)
class CompensationHint:
    """Optional structured pay signal — never invent missing amounts."""

    currency: str | None
    min_amount: int | None
    max_amount: int | None
    period: str | None  # year | month | hour | unknown


class Opportunity:
    """Normalized career opening from a permitted source."""

    def __init__(
        self,
        opportunity_id: OpportunityId,
        *,
        title: str,
        company: CompanyName,
        location: str | None,
        is_remote: bool,
        description_text: str,
        apply_url: str,
        provenance: SourceProvenance,
        dedup_key: DedupKey,
        status: OpportunityStatus,
        compensation: CompensationHint | None = None,
        posted_at: datetime | None = None,
        ingested_at: datetime | None = None,
        updated_at: datetime | None = None,
        skills: Sequence[str] | None = None,
    ) -> None:
        title_clean = title.strip()
        if not title_clean:
            raise ValidationError("Opportunity title must not be empty")
        apply = apply_url.strip()
        if not apply:
            raise ValidationError("apply_url must not be empty")

        now = datetime.now(UTC)
        self._id = opportunity_id
        self._title = title_clean
        self._company = company
        self._location = location.strip() if location and location.strip() else None
        self._is_remote = is_remote
        self._description_text = description_text.strip()
        self._apply_url = apply
        self._provenance = provenance
        self._dedup_key = dedup_key
        self._status = status
        self._compensation = compensation
        self._posted_at = posted_at
        self._ingested_at = ingested_at or now
        self._updated_at = updated_at or now
        self._skills = tuple(s.strip().lower() for s in (skills or ()) if s.strip())
        self._events: list[DomainEvent] = []

    @classmethod
    def ingest_normalized(
        cls,
        *,
        title: str,
        company: CompanyName,
        location: str | None,
        is_remote: bool,
        description_text: str,
        apply_url: str,
        provenance: SourceProvenance,
        compensation: CompensationHint | None = None,
        posted_at: datetime | None = None,
        skills: Sequence[str] | None = None,
        opportunity_id: OpportunityId | None = None,
    ) -> Opportunity:
        dedup = DedupKey.from_parts(
            company=str(company),
            title=title,
            location=location,
            apply_url=apply_url,
        )
        opp = cls(
            opportunity_id or OpportunityId.generate(),
            title=title,
            company=company,
            location=location,
            is_remote=is_remote,
            description_text=description_text,
            apply_url=apply_url,
            provenance=provenance,
            dedup_key=dedup,
            status=OpportunityStatus.ACTIVE,
            compensation=compensation,
            posted_at=posted_at,
            skills=skills,
        )
        opp._events.append(
            OpportunityActivated(
                opportunity_id=opp.id.value,
                dedup_key=str(opp.dedup_key),
                source_kind=provenance.kind.value,
            )
        )
        return opp

    def record_duplicate_of(self, existing_id: OpportunityId) -> None:
        self._events.append(
            DuplicateOpportunityCollapsed(
                opportunity_id=self.id.value,
                existing_opportunity_id=existing_id.value,
                dedup_key=str(self.dedup_key),
            )
        )

    def refresh_from(self, other: Opportunity) -> None:
        """Update mutable listing fields from a newer ingest of the same dedup key."""
        self._title = other.title
        self._company = other.company
        self._location = other.location
        self._is_remote = other.is_remote
        self._description_text = other.description_text
        self._apply_url = other.apply_url
        self._provenance = other.provenance
        self._compensation = other.compensation
        self._posted_at = other.posted_at
        self._skills = other.skills
        self._status = OpportunityStatus.ACTIVE
        self._updated_at = datetime.now(UTC)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    @property
    def id(self) -> OpportunityId:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def company(self) -> CompanyName:
        return self._company

    @property
    def location(self) -> str | None:
        return self._location

    @property
    def is_remote(self) -> bool:
        return self._is_remote

    @property
    def description_text(self) -> str:
        return self._description_text

    @property
    def apply_url(self) -> str:
        return self._apply_url

    @property
    def provenance(self) -> SourceProvenance:
        return self._provenance

    @property
    def dedup_key(self) -> DedupKey:
        return self._dedup_key

    @property
    def status(self) -> OpportunityStatus:
        return self._status

    @property
    def compensation(self) -> CompensationHint | None:
        return self._compensation

    @property
    def posted_at(self) -> datetime | None:
        return self._posted_at

    @property
    def ingested_at(self) -> datetime:
        return self._ingested_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def skills(self) -> tuple[str, ...]:
        return self._skills
