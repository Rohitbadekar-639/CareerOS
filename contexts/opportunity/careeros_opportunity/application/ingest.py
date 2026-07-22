"""Ingest + search use cases for Opportunity Discovery."""

from __future__ import annotations

from dataclasses import dataclass

from careeros_opportunity.domain.opportunity import Opportunity
from careeros_opportunity.domain.value_objects import CompanyName
from careeros_opportunity.ports.opportunity_source import (
    OpportunityRepository,
    OpportunitySearchFilter,
    OpportunitySource,
    RawOpportunityListing,
    SourceBoard,
    provenance_for,
)


@dataclass(frozen=True, slots=True)
class IngestResult:
    inserted: int
    updated: int
    collapsed: int


class IngestFromSource:
    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        source: OpportunitySource,
    ) -> None:
        self._repository = repository
        self._source = source

    def execute(self, board: SourceBoard) -> IngestResult:
        if board.kind is not self._source.kind:
            raise ValueError(f"Source {self._source.kind} cannot fetch {board.kind}")
        listings = self._source.fetch_listings(board)
        inserted = updated = collapsed = 0
        for listing in listings:
            opportunity = self._to_opportunity(board, listing)
            existing = self._repository.find_by_dedup_key(opportunity.dedup_key)
            if existing is None:
                self._repository.upsert(opportunity)
                inserted += 1
                continue
            existing.refresh_from(opportunity)
            opportunity.record_duplicate_of(existing.id)
            opportunity.pull_events()  # discard collapsed events for MVP (no bus yet)
            self._repository.upsert(existing)
            updated += 1
            collapsed += 1
        return IngestResult(inserted=inserted, updated=updated, collapsed=collapsed)

    def _to_opportunity(self, board: SourceBoard, listing: RawOpportunityListing) -> Opportunity:
        return Opportunity.ingest_normalized(
            title=listing.title,
            company=CompanyName(listing.company),
            location=listing.location,
            is_remote=listing.is_remote,
            description_text=listing.description_text,
            apply_url=listing.apply_url,
            provenance=provenance_for(board, listing),
            compensation=listing.compensation,
            posted_at=listing.posted_at,
            skills=listing.skills,
        )


class SearchOpportunities:
    def __init__(self, *, repository: OpportunityRepository) -> None:
        self._repository = repository

    def execute(self, filters: OpportunitySearchFilter) -> list[Opportunity]:
        limit = min(max(filters.limit, 1), 100)
        offset = max(filters.offset, 0)
        return self._repository.search(
            OpportunitySearchFilter(
                query=filters.query,
                location=filters.location,
                remote_only=filters.remote_only,
                company=filters.company,
                source_kind=filters.source_kind,
                limit=limit,
                offset=offset,
            )
        )


class RefreshConfiguredSources:
    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        sources: dict[str, OpportunitySource],
        boards: list[SourceBoard],
    ) -> None:
        self._repository = repository
        self._sources = sources
        self._boards = boards

    def execute(self) -> dict[str, IngestResult]:
        results: dict[str, IngestResult] = {}
        for board in self._boards:
            source = self._sources.get(board.kind.value)
            if source is None:
                continue
            key = f"{board.kind.value}:{board.board_token}"
            results[key] = IngestFromSource(repository=self._repository, source=source).execute(
                board
            )
        return results
