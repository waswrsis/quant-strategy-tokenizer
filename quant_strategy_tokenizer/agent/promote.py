"""Profile promotion helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope, ProfileLiteral
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validate import ValidationFailure, validate


class PromoteResult(BaseModel):
    """Result of a profile promotion attempt."""

    ok: bool
    new_envelope: DeploymentEnvelope | None = None
    new_validation_failures: list[ValidationFailure] = Field(default_factory=list)
    diff_from_previous: list[str] = Field(default_factory=list)


def _hash_validation_result(failures: list[ValidationFailure]) -> str:
    payload = [failure.model_dump(mode="json", exclude_none=True) for failure in failures]
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def promote(
    ir: StrategyIR,
    envelope: DeploymentEnvelope,
    target_profile: ProfileLiteral,
    approved_by: str | None = None,
) -> PromoteResult:
    """Promote by validating target profile and returning a new envelope only."""

    validation = validate(ir, profile=target_profile)
    if validation.failures:
        return PromoteResult(
            ok=False,
            new_envelope=None,
            new_validation_failures=validation.failures,
            diff_from_previous=[
                f"profile would change: {envelope.profile} -> {target_profile}",
            ],
        )

    new_envelope = DeploymentEnvelope(
        strategy_instance_hash=envelope.strategy_instance_hash,
        profile=target_profile,
        approved_by=approved_by,
        # qst-lint: disable-next-line -- promotion approval timestamp metadata
        approved_at=datetime.now(UTC) if approved_by else None,
        validation_result_hash=_hash_validation_result(validation.failures),
        notes=envelope.notes,
    )

    return PromoteResult(
        ok=True,
        new_envelope=new_envelope,
        new_validation_failures=[],
        diff_from_previous=[f"profile: {envelope.profile} -> {target_profile}"],
    )
