"""Ports for Opportunity Discovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from careeros_opportunity.domain.opportunity import CompensationHint, Opportunity
from careeros_opportunity.domain.value_objects import (
    DedupKey,
    OpportunityId,
    SourceKind,
    SourceProvenance,
)


@dataclass(frozen=True, slots=True)
class RawOpportunityListing:
    """Normalized-enough listing emitted by a source adapter (ACL boundary)."""

    title: str
    company: str
    location: str | None
    is_remote: bool
    description_text: str
    apply_url: str
    external_id: str
    source_url: str
    posted_at: datetime | None = None
    compensation: CompensationHint | None = None
    skills: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceBoard:
    kind: SourceKind
    board_token: str


@runtime_checkable
class OpportunitySource(Protocol):
    """Permitted origin adapter — fetch public listings for one board."""

    kind: SourceKind

    def fetch_listings(self, board: SourceBoard) -> list[RawOpportunityListing]: ...


@dataclass(frozen=True, slots=True)
class OpportunitySearchFilter:
    query: str | None = None
    location: str | None = None
    remote_only: bool | None = None
    company: str | None = None
    source_kind: SourceKind | None = None
    limit: int = 50
    offset: int = 0


@runtime_checkable
class OpportunityRepository(Protocol):
    def get(self, opportunity_id: OpportunityId) -> Opportunity | None: ...

    def find_by_dedup_key(self, dedup_key: DedupKey) -> Opportunity | None: ...

    def upsert(self, opportunity: Opportunity) -> Opportunity: ...

    def search(self, filters: OpportunitySearchFilter) -> list[Opportunity]: ...

    def list_active(self, *, limit: int = 500) -> list[Opportunity]: ...


def provenance_for(board: SourceBoard, listing: RawOpportunityListing) -> SourceProvenance:
    return SourceProvenance(
        kind=board.kind,
        board_token=board.board_token,
        external_id=listing.external_id,
        source_url=listing.source_url,
    )
