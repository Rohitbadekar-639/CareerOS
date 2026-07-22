"""Opportunity lifecycle states (domain-model § Opportunity)."""

from enum import StrEnum


class OpportunityStatus(StrEnum):
    INGESTED = "ingested"
    NORMALIZED = "normalized"
    ACTIVE = "active"
    STALE = "stale"
    EXPIRED = "expired"
    CLOSED = "closed"
    ARCHIVED = "archived"
