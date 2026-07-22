"""Unit tests for Application lifecycle."""

from uuid import uuid4

import pytest

from careeros_application_tracking.domain.application import Application, ApplicationStatus
from careeros_shared_kernel import ConflictError


def test_save_and_apply() -> None:
    app = Application.save_interest(user_id=uuid4(), opportunity_id=uuid4())
    assert app.status is ApplicationStatus.INTERESTED
    applied = app.mark_applied()
    assert applied.status is ApplicationStatus.APPLIED


def test_invalid_transition() -> None:
    app = Application.save_interest(user_id=uuid4(), opportunity_id=uuid4())
    with pytest.raises(ConflictError):
        app.transition_to(ApplicationStatus.OFFER)
