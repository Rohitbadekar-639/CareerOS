"""Value objects for the Opportunity context."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from careeros_shared_kernel import ValidationError

_SLUG = re.compile(r"[^a-z0-9]+")


class SourceKind(StrEnum):
    GREENHOUSE = "greenhouse"
    ASHBY = "ashby"


@dataclass(frozen=True, slots=True)
class OpportunityId:
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise ValidationError("OpportunityId must be a UUID")

    @classmethod
    def generate(cls) -> OpportunityId:
        return cls(uuid4())

    @classmethod
    def from_str(cls, raw: str) -> OpportunityId:
        try:
            return cls(UUID(raw))
        except ValueError as exc:
            raise ValidationError("Invalid OpportunityId") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class CompanyName:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValidationError("Company name must not be empty")
        object.__setattr__(self, "value", cleaned)

    def normalized(self) -> str:
        return _SLUG.sub("-", self.value.lower()).strip("-")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DedupKey:
    """Stable fingerprint used to collapse duplicate listings."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("DedupKey must not be empty")

    @classmethod
    def from_parts(
        cls,
        *,
        company: str,
        title: str,
        location: str | None,
        apply_url: str | None = None,
    ) -> DedupKey:
        company_n = _SLUG.sub("-", company.lower()).strip("-")
        title_n = _SLUG.sub("-", title.lower()).strip("-")
        location_n = _SLUG.sub("-", (location or "").lower()).strip("-")
        url_n = (apply_url or "").strip().lower()
        material = f"{company_n}|{title_n}|{location_n}|{url_n}"
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return cls(digest)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Recorded origin + legal basis for an ingested listing."""

    kind: SourceKind
    board_token: str
    external_id: str
    source_url: str
    legal_basis: str = "public_ats_board_feed"

    def __post_init__(self) -> None:
        if not self.board_token.strip():
            raise ValidationError("board_token must not be empty")
        if not self.external_id.strip():
            raise ValidationError("external_id must not be empty")
        if not self.source_url.strip():
            raise ValidationError("source_url must not be empty")
