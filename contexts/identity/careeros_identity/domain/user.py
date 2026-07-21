"""User aggregate root — identity anchor for CareerOS."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

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
from careeros_identity.domain.value_objects import (
    AuthRef,
    ConsentPurpose,
    ConsentScope,
    EmailAddress,
    UserId,
)
from careeros_shared_kernel import (
    ConflictError,
    DomainEvent,
    PermissionDeniedError,
    ValidationError,
)

_TERMINAL_OR_EXITING = frozenset(
    {
        UserStatus.SUSPENDED,
        UserStatus.DELETION_REQUESTED,
        UserStatus.ERASED,
    }
)


class User:
    """Authenticated account holder. Owns Consents; distinct from Candidate."""

    def __init__(
        self,
        user_id: UserId,
        email: EmailAddress,
        auth_ref: AuthRef,
        *,
        status: UserStatus,
        role: UserRole = UserRole.CANDIDATE,
        email_verified: bool = False,
        legal_hold: bool = False,
        consents: Sequence[Consent] | None = None,
        tenant_id: str | None = None,
        registered_at: datetime | None = None,
    ) -> None:
        if registered_at is not None and registered_at.tzinfo is None:
            raise ValidationError("User.registered_at must be timezone-aware")

        self._id = user_id
        self._email = email
        self._auth_ref = auth_ref
        self._status = status
        self._role = role
        self._email_verified = email_verified
        self._legal_hold = legal_hold
        self._consents: list[Consent] = list(consents or ())
        self._tenant_id = tenant_id
        self._registered_at = registered_at or datetime.now(UTC)
        self._events: list[DomainEvent] = []

    @classmethod
    def register(
        cls,
        email: EmailAddress,
        auth_ref: AuthRef,
        initial_consents: Sequence[ConsentScope],
        *,
        user_id: UserId | None = None,
        role: UserRole = UserRole.CANDIDATE,
        email_verified: bool = False,
        registered_at: datetime | None = None,
        tenant_id: str | None = None,
    ) -> User:
        """Create a new User with required essential-account consent.

        Emits ``UserRegistered`` and one ``ConsentGranted`` per initial scope.
        """
        scopes = list(initial_consents)
        if not any(scope.purpose is ConsentPurpose.ESSENTIAL_ACCOUNT for scope in scopes):
            raise ValidationError("Registration requires ConsentPurpose.ESSENTIAL_ACCOUNT")
        if len({scope.purpose for scope in scopes}) != len(scopes):
            raise ValidationError("Duplicate consent purposes at registration")

        at = registered_at or datetime.now(UTC)
        status = UserStatus.ACTIVE if email_verified else UserStatus.REGISTERED
        user = cls(
            user_id or UserId.generate(),
            email,
            auth_ref,
            status=status,
            role=role,
            email_verified=email_verified,
            registered_at=at,
            tenant_id=tenant_id,
        )
        user._record(
            UserRegistered(
                user_id=user.id.value,
                email=str(user.email),
                auth_ref=str(user.auth_ref),
            )
        )
        for scope in scopes:
            user._grant_consent(scope, at=at)
        return user

    @property
    def id(self) -> UserId:
        return self._id

    @property
    def email(self) -> EmailAddress:
        return self._email

    @property
    def auth_ref(self) -> AuthRef:
        return self._auth_ref

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def email_verified(self) -> bool:
        return self._email_verified

    @property
    def legal_hold(self) -> bool:
        return self._legal_hold

    @property
    def tenant_id(self) -> str | None:
        return self._tenant_id

    @property
    def registered_at(self) -> datetime:
        return self._registered_at

    @property
    def consents(self) -> tuple[Consent, ...]:
        return tuple(self._consents)

    def active_consents(self) -> tuple[Consent, ...]:
        return tuple(c for c in self._consents if c.is_active)

    def has_active_consent(self, purpose: ConsentPurpose) -> bool:
        return any(c.is_active and c.purpose is purpose for c in self._consents)

    def ensure_processing_allowed(self, purpose: ConsentPurpose) -> None:
        """Consent-gated processing policy — raise if no active matching Consent."""
        if self._status is UserStatus.ERASED:
            raise PermissionDeniedError("Erased users cannot be processed")
        if self._status is UserStatus.SUSPENDED:
            raise PermissionDeniedError("Suspended users cannot be processed")
        if not self.has_active_consent(purpose):
            raise PermissionDeniedError(f"No active consent for purpose {purpose.value}")

    def grant_consent(
        self,
        scope: ConsentScope,
        *,
        at: datetime | None = None,
    ) -> Consent:
        self._ensure_mutable()
        return self._grant_consent(scope, at=at or datetime.now(UTC))

    def withdraw_consent(
        self,
        purpose: ConsentPurpose,
        *,
        at: datetime | None = None,
    ) -> Consent:
        self._ensure_mutable()
        if purpose is ConsentPurpose.ESSENTIAL_ACCOUNT:
            raise ValidationError(
                "ESSENTIAL_ACCOUNT consent cannot be withdrawn while the account exists"
            )
        consent = self._active_consent_for(purpose)
        if consent is None:
            raise ConflictError(f"No active consent for purpose {purpose.value}")
        withdrawn_at = at or datetime.now(UTC)
        consent.withdraw(at=withdrawn_at)
        self._record(
            ConsentWithdrawn(
                user_id=self._id.value,
                consent_id=consent.id.value,
                purpose=purpose,
            )
        )
        return consent

    def verify_email(self) -> None:
        if self._status is UserStatus.ERASED:
            raise ConflictError("Cannot verify email on an erased user")
        if self._email_verified and self._status is UserStatus.ACTIVE:
            raise ConflictError("Email is already verified")
        if self._status not in {UserStatus.REGISTERED, UserStatus.ACTIVE}:
            raise ConflictError(f"Cannot verify email from status {self._status.value}")
        self._email_verified = True
        if self._status is UserStatus.REGISTERED:
            self._status = UserStatus.ACTIVE
        self._record(UserEmailVerified(user_id=self._id.value))

    def suspend(self) -> None:
        if self._status is not UserStatus.ACTIVE:
            raise ConflictError(
                f"Only ACTIVE users can be suspended (current: {self._status.value})"
            )
        self._status = UserStatus.SUSPENDED
        self._record(UserSuspended(user_id=self._id.value))

    def request_deletion(self) -> None:
        if self._status in {UserStatus.DELETION_REQUESTED, UserStatus.ERASED}:
            raise ConflictError(f"Deletion already in progress or completed ({self._status.value})")
        if self._status not in {
            UserStatus.REGISTERED,
            UserStatus.ACTIVE,
            UserStatus.SUSPENDED,
        }:
            raise ConflictError(f"Cannot request deletion from status {self._status.value}")
        self._status = UserStatus.DELETION_REQUESTED
        self._record(AccountDeletionRequested(user_id=self._id.value))

    def erase(self) -> None:
        """Complete erasure after a deletion request. Blocked under legal hold."""
        if self._legal_hold:
            raise ConflictError("Cannot erase a user under legal hold")
        if self._status is not UserStatus.DELETION_REQUESTED:
            raise ConflictError(
                f"Erase requires status deletion_requested (current: {self._status.value})"
            )
        self._status = UserStatus.ERASED
        self._record(UserErased(user_id=self._id.value))

    def place_under_legal_hold(self) -> None:
        if self._status is UserStatus.ERASED:
            raise ConflictError("Cannot place an erased user under legal hold")
        self._legal_hold = True

    def release_legal_hold(self) -> None:
        self._legal_hold = False

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def _grant_consent(self, scope: ConsentScope, *, at: datetime) -> Consent:
        if self.has_active_consent(scope.purpose):
            raise ConflictError(f"Active consent already exists for purpose {scope.purpose.value}")
        consent = Consent.grant(scope, granted_at=at)
        self._consents.append(consent)
        self._record(
            ConsentGranted(
                user_id=self._id.value,
                consent_id=consent.id.value,
                purpose=scope.purpose,
            )
        )
        return consent

    def _active_consent_for(self, purpose: ConsentPurpose) -> Consent | None:
        for consent in self._consents:
            if consent.is_active and consent.purpose is purpose:
                return consent
        return None

    def _ensure_mutable(self) -> None:
        if self._status in _TERMINAL_OR_EXITING:
            raise ConflictError(f"User in status {self._status.value} cannot change consents")

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)
