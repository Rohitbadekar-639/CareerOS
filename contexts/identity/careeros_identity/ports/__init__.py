"""Identity ports — external dependencies for the Identity & Access context."""

from careeros_identity.ports.auth_provider import AuthProvider, VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository

__all__ = [
    "AuthProvider",
    "UserRepository",
    "VerifiedIdentity",
]
