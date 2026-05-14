"""Structured verification result models for P3a-0."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

P3A0_LIMITATION_NOTE = (
    "P3 verify checks structural and trace-semantic artifacts only; numerical "
    "output equivalence is not asserted."
)


class VerificationLevel(StrEnum):
    """Verification levels surfaced by qst verify."""

    STRUCTURAL = "STRUCTURAL"
    SEMANTIC_TRACE = "SEMANTIC_TRACE"
    NUMERICAL = "NUMERICAL"


class VerifyFailure(BaseModel):
    """One structured lock verification failure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    message: str
    path: str | None = None
    expected: Any | None = None
    actual: Any | None = None


class VerifyResult(BaseModel):
    """Structured result returned by all P3 verify paths."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ok: bool
    verification_level: VerificationLevel = VerificationLevel.STRUCTURAL
    limitation_note: str = P3A0_LIMITATION_NOTE
    failures: list[VerifyFailure] = Field(default_factory=list)

    @classmethod
    def from_failures(
        cls,
        failures: list[VerifyFailure],
        *,
        verification_level: VerificationLevel = VerificationLevel.STRUCTURAL,
    ) -> VerifyResult:
        return cls(
            ok=not failures,
            verification_level=verification_level,
            failures=failures,
        )
