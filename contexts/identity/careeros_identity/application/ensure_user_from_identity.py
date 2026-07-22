"""Get-or-register the CareerOS User for a verified external identity."""

from __future__ import annotations

from careeros_identity.domain.lifecycle import UserStatus
from careeros_identity.domain.user import User
from careeros_identity.domain.value_objects import ConsentPurpose, ConsentScope
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository


class EnsureUserFromIdentity:
    """Application use case: map Supabase identity → our User aggregate."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, identity: VerifiedIdentity) -> User:
        existing = self._users.get_by_auth_ref(identity.auth_ref)
        if existing is not None:
            return self._refresh_verification(existing, identity)

        user = User.register(
            identity.email,
            identity.auth_ref,
            [ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT)],
            email_verified=identity.email_verified,
        )
        user.pull_events()
        self._users.save(user)
        return user

    def _refresh_verification(self, user: User, identity: VerifiedIdentity) -> User:
        if (
            identity.email_verified
            and not user.email_verified
            and user.status in {UserStatus.REGISTERED, UserStatus.ACTIVE}
        ):
            user.verify_email()
            user.pull_events()
            self._users.save(user)
        return user
