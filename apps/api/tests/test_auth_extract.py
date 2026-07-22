import pytest
from starlette.requests import Request

from careeros_api.auth import extract_bearer_token
from careeros_shared_kernel import PermissionDeniedError


def test_extract_bearer_token() -> None:
    request = Request(
        {
            "type": "http",
            "headers": [(b"authorization", b"Bearer abc.def.ghi")],
        }
    )
    assert extract_bearer_token(request) == "abc.def.ghi"


def test_extract_bearer_token_rejects_missing() -> None:
    request = Request({"type": "http", "headers": []})
    with pytest.raises(PermissionDeniedError):
        extract_bearer_token(request)
