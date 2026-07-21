"""Consent entity — purpose-scoped permission owned by the User aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_identity.domain.value_objects import ConsentId, ConsentPurpose, ConsentScope
from careeros_shared_kernel import ConflictError, ValidationError


class Consent:
    """Purpose-scoped permission. Processing is illegal without an active Consent."""

    def __init__(
        self,
        consent_id: ConsentId,
        scope: ConsentScope,
        *,
        granted_at: datetime,
        withdrawn_at: datetime | None = None,
    ) -> None:
        if granted_at.tzinfo is None:
            raise ValidationError("Consent.granted_at must be timezone-aware")
        if withdrawn_at is not None and withdrawn_at.tzinfo is None:
            raise ValidationError("Consent.withdrawn_at must be timezone-aware")
        if withdrawn_at is not None and withdrawn_at < granted_at:
            raise ValidationError("Consent.withdrawn_at cannot precede granted_at")

        self._id = consent_id
        self._scope = scope
        self._granted_at = granted_at
        self._withdrawn_at = withdrawn_at

    @classmethod
    def grant(
        cls,
        scope: ConsentScope,
        *,
        consent_id: ConsentId | None = None,
        granted_at: datetime | None = None,
    ) -> Consent:
        return cls(
            consent_id or ConsentId.generate(),
            scope,
            granted_at=granted_at or datetime.now(UTC),
        )

    @property
    def id(self) -> ConsentId:
        return self._id

    @property
    def scope(self) -> ConsentScope:
        return self._scope

    @property
    def purpose(self) -> ConsentPurpose:
        return self._scope.purpose

    @property
    def granted_at(self) -> datetime:
        return self._granted_at

    @property
    def withdrawn_at(self) -> datetime | None:
        return self._withdrawn_at

    @property
    def is_active(self) -> bool:
        return self._withdrawn_at is None

    def withdraw(self, *, at: datetime | None = None) -> None:
        if not self.is_active:
            raise ConflictError(
                f"Consent {self._id} for {self._scope.purpose} is already withdrawn"
            )
        withdrawn_at = at or datetime.now(UTC)
        if withdrawn_at.tzinfo is None:
            raise ValidationError("Consent withdrawal time must be timezone-aware")
        if withdrawn_at < self._granted_at:
            raise ValidationError("Consent.withdrawn_at cannot precede granted_at")
        self._withdrawn_at = withdrawn_at
