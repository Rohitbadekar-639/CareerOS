from datetime import UTC, datetime
from uuid import uuid4

import pytest

from careeros_identity.domain import (
    AuthRef,
    Consent,
    ConsentId,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    UserId,
)
from careeros_shared_kernel import ConflictError, ValidationError


def test_user_id_generate_and_round_trip() -> None:
    user_id = UserId.generate()
    assert UserId.from_raw(str(user_id)) == user_id
    assert UserId.from_raw(user_id.value) == user_id


def test_user_id_rejects_invalid() -> None:
    with pytest.raises(ValidationError):
        UserId.from_raw("not-a-uuid")


def test_email_normalizes_and_validates() -> None:
    assert EmailAddress("  Alex@Example.COM ").value == "alex@example.com"


def test_email_rejects_invalid() -> None:
    with pytest.raises(ValidationError):
        EmailAddress("not-an-email")
    with pytest.raises(ValidationError):
        EmailAddress("")


def test_auth_ref_rejects_blank() -> None:
    with pytest.raises(ValidationError):
        AuthRef("   ")


def test_consent_grant_and_withdraw() -> None:
    granted_at = datetime(2026, 1, 1, tzinfo=UTC)
    consent = Consent.grant(
        ConsentScope(ConsentPurpose.NOTIFICATIONS),
        consent_id=ConsentId.generate(),
        granted_at=granted_at,
    )
    assert consent.is_active
    assert consent.purpose is ConsentPurpose.NOTIFICATIONS

    withdrawn_at = datetime(2026, 1, 2, tzinfo=UTC)
    consent.withdraw(at=withdrawn_at)
    assert consent.withdrawn_at == withdrawn_at
    assert consent.is_active is False


def test_consent_cannot_withdraw_twice() -> None:
    consent = Consent.grant(ConsentScope(ConsentPurpose.PROFILE_PROCESSING))
    consent.withdraw()
    with pytest.raises(ConflictError):
        consent.withdraw()


def test_consent_requires_aware_timestamps() -> None:
    with pytest.raises(ValidationError):
        Consent(
            ConsentId(uuid4()),
            ConsentScope(ConsentPurpose.ESSENTIAL_ACCOUNT),
            granted_at=datetime(2026, 1, 1),
        )
