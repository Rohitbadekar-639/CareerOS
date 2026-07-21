"""User lifecycle and role enums (Identity & Access)."""

from enum import StrEnum


class UserStatus(StrEnum):
    """User aggregate lifecycle (Domain Model §4 IAM)."""

    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETION_REQUESTED = "deletion_requested"
    ERASED = "erased"


class UserRole(StrEnum):
    """MVP roles (Technical Architecture §5). Reserved roles are not used yet."""

    CANDIDATE = "candidate"
    ADMIN = "admin"
