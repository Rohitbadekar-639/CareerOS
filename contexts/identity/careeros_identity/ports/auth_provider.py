"""AuthProvider port — verify external identity tokens (Supabase Auth)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from careeros_identity.domain.value_objects import AuthRef, EmailAddress


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """Claims extracted from a verified access token.

    ``auth_ref`` maps to our ``AuthRef`` (provider subject). Our ``User``
    aggregate remains the source of truth; this is only the external handle.
    """

    auth_ref: AuthRef
    email: EmailAddress
    email_verified: bool


@runtime_checkable
class AuthProvider(Protocol):
    def verify_access_token(self, token: str) -> VerifiedIdentity:
        """Verify a bearer access token and return identity claims.

        Raises ``PermissionDeniedError`` when the token is missing, malformed,
        expired, or fails signature/issuer/audience checks.
        """
        ...
