"""Receipt-backed strategy-memory and backtest admission decisions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, evidence_identity
from qst.hash.common import HashString
from qst.receipts import (
    ExperimentReceipt,
    StrategyRecordReceipt,
    experiment_identity,
    strategy_receipt_identity,
)


class AdmissionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-admission-decision/2.0"] = "qst-admission-decision/2.0"
    admission_type: Literal["strategy_memory", "backtested_claim"]
    allowed: bool
    subject_ref: str
    receipt_ids: tuple[HashString, ...] = ()
    reason_codes: tuple[str, ...]

    @field_validator("receipt_ids", "reason_codes", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


def admit_strategy_memory(receipt: StrategyRecordReceipt) -> AdmissionDecision:
    reasons: list[str] = []
    sealed = (
        receipt.strategy_receipt_id is not None
        and receipt.strategy_receipt_id == strategy_receipt_identity(receipt)
    )
    if not sealed:
        reasons.append("QST_STRATEGY_MEMORY_RECEIPT_INVALID")
    if not receipt.validation_ok:
        reasons.append("QST_STRATEGY_MEMORY_VALIDATION_FAILED")
    if not receipt.non_goals:
        reasons.append("QST_STRATEGY_MEMORY_NON_GOALS_REQUIRED")
    allowed = not reasons
    if allowed:
        reasons.append("QST_STRATEGY_MEMORY_ADMITTED")
    return AdmissionDecision(
        admission_type="strategy_memory",
        allowed=allowed,
        subject_ref=receipt.strategy_hash,
        receipt_ids=(receipt.strategy_receipt_id,) if receipt.strategy_receipt_id else (),
        reason_codes=tuple(reasons),
    )


def admit_backtested_claim(
    receipt: ExperimentReceipt, evidence: tuple[EvidenceEnvelope, ...]
) -> AdmissionDecision:
    reasons: list[str] = []
    sealed = receipt.experiment_hash is not None and receipt.experiment_hash == experiment_identity(
        receipt
    )
    if not sealed:
        reasons.append("QST_BACKTEST_EXPERIMENT_RECEIPT_INVALID")
    verified_ids = {
        item.evidence_id
        for item in evidence
        if item.evidence_id is not None
        and item.evidence_id == evidence_identity(item)
        and item.subject_ref == receipt.subject_ref
        and isinstance(item.payload, ResultEvidencePayload)
        and item.payload.collection_status == "verified"
    }
    if not set(receipt.result_evidence_ids).issubset(verified_ids):
        reasons.append("QST_BACKTEST_RESULT_EVIDENCE_UNVERIFIED")
    allowed = not reasons
    if allowed:
        reasons.append("QST_BACKTEST_CLAIM_ADMITTED")
    return AdmissionDecision(
        admission_type="backtested_claim",
        allowed=allowed,
        subject_ref=receipt.subject_ref,
        receipt_ids=(receipt.experiment_hash,) if receipt.experiment_hash else (),
        reason_codes=tuple(reasons),
    )
