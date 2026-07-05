from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from qst.admission import admit_backtested_claim, admit_strategy_memory
from qst.claims import ClaimPolicy, EvidenceRequirement, evaluate_claim, seal_claim_policy
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, seal_evidence
from qst.ir import load_ir_v04_file
from qst.receipts import (
    AgentReceipt,
    EvaluationWindow,
    ExperimentReceipt,
    build_strategy_record_receipt,
    seal_agent_receipt,
    seal_experiment_receipt,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
NOW = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
STRATEGY = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "strategies"
    / "01_ema_cross"
    / "strategy.gkr.yaml"
)


def _result_evidence() -> EvidenceEnvelope:
    return seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:receipt-v2",
            observed_at=NOW,
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="verified",
                artifact_ids=(HASH_B,),
            ),
        )
    )


def _experiment(evidence: EvidenceEnvelope) -> ExperimentReceipt:
    assert evidence.evidence_id is not None
    return seal_experiment_receipt(
        ExperimentReceipt(
            subject_ref=evidence.subject_ref,
            strategy_receipt_id=HASH_A,
            strategy_hash=HASH_B,
            data_snapshot_ids=(HASH_C,),
            evaluation_window=EvaluationWindow(
                start=date(2025, 1, 1), end=date(2025, 12, 31)
            ),
            evaluator_adapter_id="external.backtester",
            evaluator_adapter_version="2.4.0",
            parameters={"window": 20},
            costs={"commission_rate": 0.001},
            slippage={"model": "fixed_bps", "bps": 2},
            seeds=(7,),
            metric_definitions={"sharpe": "annualized excess-return Sharpe ratio"},
            result_evidence_ids=(evidence.evidence_id,),
        )
    )


def test_complete_canonical_strategy_identity_covers_metadata() -> None:
    ir = load_ir_v04_file(STRATEGY)
    first = build_strategy_record_receipt(
        ir, non_goals=("no execution", "no profitability claim")
    )
    changed = ir.model_copy(update={"metadata": {**ir.metadata, "review_note": "changed"}})
    second = build_strategy_record_receipt(
        changed, non_goals=("no execution", "no profitability claim")
    )
    assert first.strategy_hash != second.strategy_hash
    assert first.graph_hash == second.graph_hash
    assert first.strategy_receipt_id != second.strategy_receipt_id

    admitted = admit_strategy_memory(first)
    assert admitted.allowed
    tampered = first.model_copy(update={"validation_ok": False})
    rejected = admit_strategy_memory(tampered)
    assert not rejected.allowed
    assert "QST_STRATEGY_MEMORY_RECEIPT_INVALID" in rejected.reason_codes


def test_experiment_and_agent_receipts_require_complete_identity_material() -> None:
    evidence = _result_evidence()
    experiment = _experiment(evidence)
    assert experiment.experiment_hash is not None
    agent = seal_agent_receipt(
        AgentReceipt(
            experiment_hash=experiment.experiment_hash,
            agent_actor_id=HASH_A,
            model_id="research-agent",
            model_version="2026-07",
            tool_versions={"qst": "1.0.0a2"},
            prompt_ref="prompt:review-v2",
            task_ref="task:investment-review",
            approval_ids=(HASH_B,),
            output_artifact_ids=(HASH_C,),
            recommendation={"decision": "human_review"},
        )
    )
    assert experiment.schema_version == "qst-experiment-receipt/2.0"
    assert agent.schema_version == "qst-agent-receipt/2.0"
    with pytest.raises(ValidationError):
        ExperimentReceipt.model_validate(
            {
                **experiment.model_dump(mode="json", exclude={"experiment_hash", "slippage"})
            }
        )


def test_backtested_claim_is_globally_receipt_gated() -> None:
    evidence = _result_evidence()
    receipt = _experiment(evidence)
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="backtested-v2",
            policy_version=2,
            claim_type="backtested",
            required_receipt_type="experiment",
            requirements=(
                EvidenceRequirement(payload_kind="result", require_verified_result=True),
            ),
        )
    )
    denied = evaluate_claim(
        policy,
        (evidence,),
        (),
        subject_ref=evidence.subject_ref,
        evaluated_at=NOW,
    )
    allowed = evaluate_claim(
        policy,
        (evidence,),
        (),
        subject_ref=evidence.subject_ref,
        evaluated_at=NOW,
        experiment_receipts=(receipt,),
    )
    assert not denied.allowed
    assert "QST_CLAIM_EXPERIMENT_RECEIPT_REQUIRED" in denied.reason_codes
    assert allowed.allowed
    assert allowed.receipt_ids == (receipt.experiment_hash,)

    admission = admit_backtested_claim(receipt, (evidence,))
    assert admission.allowed
    assert not admit_backtested_claim(receipt, ()).allowed


def test_backtested_policy_cannot_disable_receipt_gate() -> None:
    with pytest.raises(ValidationError, match="requires an experiment receipt"):
        ClaimPolicy(
            policy_id="unsafe-backtest-policy",
            policy_version=2,
            claim_type="backtested",
            requirements=(EvidenceRequirement(payload_kind="result"),),
        )

    with pytest.raises(ValidationError, match="verified result evidence"):
        ClaimPolicy(
            policy_id="unsafe-result-policy",
            policy_version=2,
            claim_type="backtested",
            required_receipt_type="experiment",
            requirements=(EvidenceRequirement(payload_kind="plan"),),
        )
