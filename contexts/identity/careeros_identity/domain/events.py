"""IAM domain events — past-tense, versioned facts (Domain Model §7)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from careeros_identity.domain.value_objects import ConsentPurpose
from careeros_shared_kernel import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class UserRegistered(DomainEvent):
    user_id: UUID
    email: str
    auth_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class UserEmailVerified(DomainEvent):
    user_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ConsentGranted(DomainEvent):
    user_id: UUID
    consent_id: UUID
    purpose: ConsentPurpose


@dataclass(frozen=True, slots=True, kw_only=True)
class ConsentWithdrawn(DomainEvent):
    user_id: UUID
    consent_id: UUID
    purpose: ConsentPurpose


@dataclass(frozen=True, slots=True, kw_only=True)
class UserSuspended(DomainEvent):
    user_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class AccountDeletionRequested(DomainEvent):
    user_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class UserErased(DomainEvent):
    user_id: UUID
