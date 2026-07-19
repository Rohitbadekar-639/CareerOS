"""Base error taxonomy for the domain.

These are expected, typed failures raised inside the domain and mapped to safe
transport responses at the boundary (problem-details). They never carry
transport or vendor detail.
"""


class DomainError(Exception):
    """Base class for all expected domain errors."""


class ValidationError(DomainError):
    """A domain invariant or input constraint was violated."""


class NotFoundError(DomainError):
    """A referenced aggregate or entity does not exist."""


class ConflictError(DomainError):
    """The operation conflicts with current state (e.g., a duplicate)."""


class PermissionDeniedError(DomainError):
    """The actor is not permitted to perform the operation."""
