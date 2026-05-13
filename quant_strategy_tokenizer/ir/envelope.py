"""Deployment envelope models for profile-specific execution context."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ProfileLiteral = Literal["research", "paper", "pretrade", "production_guarded"]


class DeploymentEnvelope(BaseModel):
    """Metadata kept outside Strategy Content IR."""

    model_config = ConfigDict(extra="forbid")

    strategy_instance_hash: str
    profile: ProfileLiteral = "research"
    approved_by: str | None = None
    approved_at: datetime | None = None
    validation_result_hash: str | None = None
    notes: str = ""
