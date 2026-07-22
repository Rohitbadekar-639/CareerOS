"""Domain events for Opportunity Discovery."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from careeros_shared_kernel import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class OpportunityActivated(DomainEvent):
    opportunity_id: UUID
    dedup_key: str
    source_kind: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DuplicateOpportunityCollapsed(DomainEvent):
    opportunity_id: UUID
    existing_opportunity_id: UUID
    dedup_key: str
