"""Identity domain: User aggregate, Consent, value objects, events."""

from careeros_identity.domain.consent import Consent
from careeros_identity.domain.events import (
    AccountDeletionRequested,
    ConsentGranted,
    ConsentWithdrawn,
    UserEmailVerified,
    UserErased,
    UserRegistered,
    UserSuspended,
)
from careeros_identity.domain.lifecycle import UserRole, UserStatus
from careeros_identity.domain.user import User
from careeros_identity.domain.value_objects import (
    AuthRef,
    ConsentId,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    UserId,
)

__all__ = [
    "AccountDeletionRequested",
    "AuthRef",
    "Consent",
    "ConsentGranted",
    "ConsentId",
    "ConsentPurpose",
    "ConsentScope",
    "ConsentWithdrawn",
    "EmailAddress",
    "User",
    "UserEmailVerified",
    "UserErased",
    "UserId",
    "UserRegistered",
    "UserRole",
    "UserStatus",
    "UserSuspended",
]
