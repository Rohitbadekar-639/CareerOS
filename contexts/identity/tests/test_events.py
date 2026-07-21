from careeros_identity.domain.events import (
    AccountDeletionRequested,
    ConsentGranted,
    ConsentWithdrawn,
    UserEmailVerified,
    UserErased,
    UserRegistered,
    UserSuspended,
)
from careeros_identity.domain.value_objects import ConsentPurpose
from careeros_shared_kernel import DomainEvent


def test_iam_events_are_domain_events() -> None:
    assert issubclass(UserRegistered, DomainEvent)
    assert issubclass(UserEmailVerified, DomainEvent)
    assert issubclass(ConsentGranted, DomainEvent)
    assert issubclass(ConsentWithdrawn, DomainEvent)
    assert issubclass(UserSuspended, DomainEvent)
    assert issubclass(AccountDeletionRequested, DomainEvent)
    assert issubclass(UserErased, DomainEvent)


def test_consent_granted_carries_purpose() -> None:
    from uuid import uuid4

    event = ConsentGranted(
        user_id=uuid4(),
        consent_id=uuid4(),
        purpose=ConsentPurpose.OPPORTUNITY_MATCHING,
    )
    assert event.purpose is ConsentPurpose.OPPORTUNITY_MATCHING
    assert event.event_version == 1
