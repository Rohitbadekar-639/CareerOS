"""Unit tests for EnsureUserFromIdentity."""

from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.domain import (
    AuthRef,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    User,
    UserStatus,
)
from careeros_identity.domain.value_objects import UserId
from careeros_identity.ports.auth_provider import VerifiedIdentity


class _Repo:
    def __init__(self) -> None:
        self.saved: list[User] = []
        self.existing: User | None = None

    def get(self, user_id: UserId) -> User | None:
        if self.existing and self.existing.id == user_id:
            return self.existing
        return None

    def get_by_auth_ref(self, auth_ref: AuthRef) -> User | None:
        if self.existing and self.existing.auth_ref == auth_ref:
            return self.existing
        return None

    def save(self, user: User) -> None:
        self.saved.append(user)
        self.existing = user


def test_registers_new_user() -> None:
    repo = _Repo()
    identity = VerifiedIdentity(
        auth_ref=AuthRef("sub-1"),
        email=EmailAddress("new@example.com"),
        email_verified=True,
    )
    user = EnsureUserFromIdentity(repo).execute(identity)
    assert user.status is UserStatus.ACTIVE
    assert len(repo.saved) == 1
    assert user.has_active_consent(ConsentPurpose.ESSENTIAL_ACCOUNT)


def test_returns_existing_without_recreating() -> None:
    repo = _Repo()
    existing = User.register(
        EmailAddress("old@example.com"),
        AuthRef("sub-2"),
        [ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT)],
        email_verified=False,
    )
    existing.pull_events()
    repo.existing = existing

    identity = VerifiedIdentity(
        auth_ref=AuthRef("sub-2"),
        email=EmailAddress("old@example.com"),
        email_verified=True,
    )
    user = EnsureUserFromIdentity(repo).execute(identity)
    assert user.id == existing.id
    assert user.email_verified is True
    assert len(repo.saved) == 1
