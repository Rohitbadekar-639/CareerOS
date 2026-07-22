"""Identity HTTP schemas (transport DTOs only — no domain leakage)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    status: str
    role: str
    email_verified: bool = Field(description="Whether the account email is verified")
