import pytest

from careeros_shared_kernel.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


@pytest.mark.parametrize(
    "error_type",
    [ValidationError, NotFoundError, ConflictError, PermissionDeniedError],
)
def test_domain_errors_subclass_base(error_type: type[DomainError]) -> None:
    assert issubclass(error_type, DomainError)


def test_domain_error_is_catchable_as_base() -> None:
    with pytest.raises(DomainError):
        raise NotFoundError("candidate 123 not found")


def test_domain_error_carries_message() -> None:
    error = ValidationError("email is required")
    assert str(error) == "email is required"
