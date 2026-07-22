"""Opportunity Discovery — ingest, normalize, deduplicate, search."""

from careeros_opportunity.domain.lifecycle import OpportunityStatus
from careeros_opportunity.domain.opportunity import Opportunity
from careeros_opportunity.domain.value_objects import (
    CompanyName,
    DedupKey,
    OpportunityId,
    SourceKind,
    SourceProvenance,
)

__all__ = [
    "CompanyName",
    "DedupKey",
    "Opportunity",
    "OpportunityId",
    "OpportunityStatus",
    "SourceKind",
    "SourceProvenance",
]
