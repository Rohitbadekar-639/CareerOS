import pytest

from careeros_identity.domain import (
    AccountDeletionRequested,
    AuthRef,
    ConsentGranted,
    ConsentPurpose,
    ConsentScope,
    ConsentWithdrawn,
    EmailAddress,
    User,
    UserEmailVerified,
    UserErased,
    UserRegistered,
    UserStatus,
    UserSuspended,
)
from careeros_shared_kernel import ConflictError, PermissionDeniedError, ValidationError


def _scopes(*purposes: ConsentPurpose) -> list[ConsentScope]:
    return [ConsentScope(purpose) for purpose in purposes]


def _register(
    *,
    email_verified: bool = False,
    purposes: tuple[ConsentPurpose, ...] = (ConsentPurpose.ESSENTIAL_ACCOUNT,),
) -> User:
    return User.register(
        EmailAddress("candidate@example.com"),
        AuthRef("supabase-user-abc"),
        _scopes(*purposes),
        email_verified=email_verified,
    )


def test_register_requires_essential_consent() -> None:
    with pytest.raises(ValidationError, match="ESSENTIAL_ACCOUNT"):
        User.register(
            EmailAddress("candidate@example.com"),
            AuthRef("supabase-user-abc"),
            _scopes(ConsentPurpose.NOTIFICATIONS),
        )


def test_register_emits_user_registered_and_consent_granted() -> None:
    user = _register(
        purposes=(
            ConsentPurpose.ESSENTIAL_ACCOUNT,
            ConsentPurpose.OPPORTUNITY_MATCHING,
        )
    )
    assert user.status is UserStatus.REGISTERED
    assert not user.email_verified
    assert user.has_active_consent(ConsentPurpose.ESSENTIAL_ACCOUNT)
    assert user.has_active_consent(ConsentPurpose.OPPORTUNITY_MATCHING)

    events = user.pull_events()
    assert isinstance(events[0], UserRegistered)
    assert events[0].email == "candidate@example.com"
    assert events[0].auth_ref == "supabase-user-abc"
    granted = [e for e in events if isinstance(e, ConsentGranted)]
    assert len(granted) == 2
    assert user.pull_events() == []


def test_register_with_verified_email_starts_active() -> None:
    user = _register(email_verified=True)
    assert user.status is UserStatus.ACTIVE
    assert user.email_verified


def test_register_rejects_duplicate_purposes() -> None:
    with pytest.raises(ValidationError, match="Duplicate"):
        _register(
            purposes=(
                ConsentPurpose.ESSENTIAL_ACCOUNT,
                ConsentPurpose.ESSENTIAL_ACCOUNT,
            )
        )


def test_verify_email_activates_registered_user() -> None:
    user = _register()
    user.pull_events()
    user.verify_email()
    assert user.status is UserStatus.ACTIVE
    assert user.email_verified
    events = user.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], UserEmailVerified)


def test_grant_and_withdraw_consent() -> None:
    user = _register()
    user.pull_events()
    user.grant_consent(ConsentScope(ConsentPurpose.NOTIFICATIONS))
    assert user.has_active_consent(ConsentPurpose.NOTIFICATIONS)
    granted = user.pull_events()
    assert isinstance(granted[0], ConsentGranted)

    user.withdraw_consent(ConsentPurpose.NOTIFICATIONS)
    assert not user.has_active_consent(ConsentPurpose.NOTIFICATIONS)
    withdrawn = user.pull_events()
    assert isinstance(withdrawn[0], ConsentWithdrawn)


def test_cannot_withdraw_essential_consent() -> None:
    user = _register()
    with pytest.raises(ValidationError, match="ESSENTIAL_ACCOUNT"):
        user.withdraw_consent(ConsentPurpose.ESSENTIAL_ACCOUNT)


def test_cannot_grant_duplicate_active_consent() -> None:
    user = _register()
    with pytest.raises(ConflictError):
        user.grant_consent(ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT))


def test_ensure_processing_allowed() -> None:
    user = _register(purposes=(ConsentPurpose.ESSENTIAL_ACCOUNT,))
    user.ensure_processing_allowed(ConsentPurpose.ESSENTIAL_ACCOUNT)
    with pytest.raises(PermissionDeniedError):
        user.ensure_processing_allowed(ConsentPurpose.OPPORTUNITY_MATCHING)


def test_suspend_and_block_processing() -> None:
    user = _register(email_verified=True)
    user.pull_events()
    user.suspend()
    assert user.status is UserStatus.SUSPENDED
    assert isinstance(user.pull_events()[0], UserSuspended)
    with pytest.raises(PermissionDeniedError, match="Suspended"):
        user.ensure_processing_allowed(ConsentPurpose.ESSENTIAL_ACCOUNT)


def test_deletion_and_erase_happy_path() -> None:
    user = _register(email_verified=True)
    user.pull_events()
    user.request_deletion()
    assert user.status == UserStatus.DELETION_REQUESTED
    assert isinstance(user.pull_events()[0], AccountDeletionRequested)

    user.erase()
    # Re-read via a wide local to avoid mypy property narrowing across mutations.
    status: UserStatus = user.status
    assert status == UserStatus.ERASED
    events = user.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], UserErased)


def test_erase_blocked_under_legal_hold() -> None:
    user = _register(email_verified=True)
    user.request_deletion()
    user.place_under_legal_hold()
    with pytest.raises(ConflictError, match="legal hold"):
        user.erase()


def test_cannot_change_consents_after_deletion_requested() -> None:
    user = _register(email_verified=True)
    user.request_deletion()
    with pytest.raises(ConflictError):
        user.grant_consent(ConsentScope(ConsentPurpose.NOTIFICATIONS))


def test_suspended_user_may_request_deletion() -> None:
    user = _register(email_verified=True)
    user.suspend()
    user.request_deletion()
    assert user.status is UserStatus.DELETION_REQUESTED
