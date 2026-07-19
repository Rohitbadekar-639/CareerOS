import pytest

from careeros_shared_kernel.result import Err, Ok, UnwrapError


def test_ok_reports_success() -> None:
    result = Ok(42)
    assert result.is_ok()
    assert not result.is_err()
    assert result.unwrap() == 42


def test_err_reports_failure() -> None:
    result = Err("boom")
    assert result.is_err()
    assert not result.is_ok()
    assert result.unwrap_err() == "boom"


def test_unwrap_on_err_raises() -> None:
    with pytest.raises(UnwrapError):
        Err("boom").unwrap()


def test_unwrap_err_on_ok_raises() -> None:
    with pytest.raises(UnwrapError):
        Ok(1).unwrap_err()


def test_unwrap_or_returns_default_on_err() -> None:
    assert Err("boom").unwrap_or(0) == 0
    assert Ok(5).unwrap_or(0) == 5


def test_ok_is_immutable() -> None:
    result = Ok(1)
    with pytest.raises(AttributeError):
        result.value = 2  # type: ignore[misc]
