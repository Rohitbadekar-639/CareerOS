"""Identity value objects — immutable and identity-free (except typed IDs)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from careeros_shared_kernel import ValidationError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class UserId:
    value: UUID

    @classmethod
    def generate(cls) -> UserId:
        return cls(uuid4())

    @classmethod
    def from_raw(cls, raw: str | UUID) -> UserId:
        if isinstance(raw, UUID):
            return cls(raw)
        try:
            return cls(UUID(raw))
        except ValueError as exc:
            raise ValidationError(f"Invalid UserId: {raw!r}") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ConsentId:
    value: UUID

    @classmethod
    def generate(cls) -> ConsentId:
        return cls(uuid4())

    @classmethod
    def from_raw(cls, raw: str | UUID) -> ConsentId:
        if isinstance(raw, UUID):
            return cls(raw)
        try:
            return cls(UUID(raw))
        except ValueError as exc:
            raise ValidationError(f"Invalid ConsentId: {raw!r}") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized or not _EMAIL_PATTERN.match(normalized):
            raise ValidationError(f"Invalid email address: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AuthRef:
    """External identity provider subject (e.g. Supabase user id). Not our UserId."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValidationError("AuthRef must not be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


class ConsentPurpose(StrEnum):
    """Purpose-scoped processing permissions (DPDP purpose limitation)."""

    ESSENTIAL_ACCOUNT = "essential_account"
    PROFILE_PROCESSING = "profile_processing"
    OPPORTUNITY_MATCHING = "opportunity_matching"
    NOTIFICATIONS = "notifications"


@dataclass(frozen=True, slots=True)
class ConsentScope:
    purpose: ConsentPurpose
