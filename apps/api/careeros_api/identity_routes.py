"""Identity HTTP route handlers — thin translation only (logic in application)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from careeros_api.deps import get_user_repository, require_verified_identity
from careeros_identity.api.schemas import MeResponse
from careeros_identity.application import EnsureUserFromIdentity
from careeros_identity.domain.user import User
from careeros_identity.ports.auth_provider import VerifiedIdentity
from careeros_identity.ports.user_repository import UserRepository

identity_router = APIRouter(prefix="/v1", tags=["identity"])


def _me_response(user: User) -> MeResponse:
    return MeResponse(
        id=user.id.value,
        email=str(user.email),
        status=user.status.value,
        role=user.role.value,
        email_verified=user.email_verified,
    )


@identity_router.get(
    "/me",
    response_model=MeResponse,
    summary="Current authenticated user",
    operation_id="getMe",
)
def get_me(
    identity: Annotated[VerifiedIdentity, Depends(require_verified_identity)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> MeResponse:
    """Return the CareerOS User for the bearer token; create on first call."""
    user = EnsureUserFromIdentity(users).execute(identity)
    return _me_response(user)
