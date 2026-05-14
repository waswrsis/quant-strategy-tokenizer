"""Validation result models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationFailure(BaseModel):
    """One validator failure or warning."""

    kind: str
    message: str
    node_id: str | None = None
    severity: str | None = None
    repair_hint: dict[str, Any] | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Aggregate validator result."""

    failures: list[ValidationFailure] = Field(default_factory=list)
    warnings: list[ValidationFailure] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures
