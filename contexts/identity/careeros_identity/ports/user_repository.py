"""UserRepository port — persistence for the User aggregate."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from careeros_identity.domain.user import User
from careeros_identity.domain.value_objects import AuthRef, UserId


@runtime_checkable
class UserRepository(Protocol):
    def get(self, user_id: UserId) -> User | None:
        """Load a User by id, or ``None`` if not found / not visible under RLS."""
        ...

    def get_by_auth_ref(self, auth_ref: AuthRef) -> User | None:
        """Load a User by external auth subject, or ``None`` if not found.

        Implementations may use a constrained RLS session variable
        (``app.current_auth_ref``) rather than a full bypass.
        """
        ...

    def save(self, user: User) -> None:
        """Persist the User aggregate (user row + consent history) atomically."""
        ...
