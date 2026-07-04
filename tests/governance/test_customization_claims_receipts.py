from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from qst.adapters.ai4finance import ADAPTER_TYPES, FinRobotEvidenceAdapter
from qst.attestations import Attestation, seal_attestation
from qst.claims import ClaimPolicy, EvidenceRequirement, evaluate_claim, seal_claim_policy
from qst.collectors import verified_result_evidence
from qst.customization import (
    CustomizationDeclaration,
    CustomizationOperation,
    apply_customizations,
    seal_customization,
    verify_declared_customization,
)
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, seal_evidence
from qst.identity import identity_hash
from qst.provenance import ActivityRecord, seal_activity
from qst.receipts import (
    AgentReceipt,
    ExperimentReceipt,
    seal_agent_receipt,
    seal_experiment_receipt,
)
from qst.storage import ContentAddressedStore

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


def _customization(base: dict, *, approval_required: bool = True):
    return seal_customization(
        CustomizationDeclaration(
            requested_by_actor_id=HASH_A,
            authored_by_actor_id=HASH_B,
            scope="strategy.parameters",
            rationale="Declared project-specific threshold",
            base_identity=identity_hash("qst:customization-base:v1", base),
            operations=(CustomizationOperation(path="/params/threshold", value=2),),
            identity_impact="derived_identity_changes",
            risk="medium",
            approval_required=approval_required,
            declared_at=NOW,
        )
    )


def test_customization_requires_approval_and_never_mutates_base() -> None:
    base = {"params": {"threshold": 1}, "name": "base"}
    declaration = _customization(base)
    with pytest.raises(ValueError, match="explicit approval"):
        apply_customizations(base, (declaration,))
    result = apply_customizations(
        base, (declaration,), approvals={declaration.customization_id: HASH_C}
    )
    assert base["params"]["threshold"] == 1
    assert result.value["params"]["threshold"] == 2
    assert result.approval_ids == (HASH_C,)


def test_undeclared_customization_is_rejected() -> None:
    base = {"params": {"threshold": 1}}
    declaration = _customization(base, approval_required=False)
    expected = apply_customizations(base, (declaration,))
    verify_declared_customization(base, expected.value, (declaration,))
    with pytest.raises(ValueError, match="undeclared customization"):
        verify_declared_customization(
            base, {"params": {"threshold": 2}, "hidden": True}, (declaration,)
        )


def _claim_inputs(maturity: str):
    evidence = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:1",
            observed_at=NOW,
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="verified",
                artifact_ids=(HASH_B,),
            ),
        )
    )
    attestation = seal_attestation(
        Attestation(
            issuer_actor_id=HASH_C,
            subject_evidence_ids=(evidence.evidence_id,),
            predicate_type="qst.adapter-verification/1.0",
            statement={"adapter_id": "fixture", "maturity": maturity, "verified": True},
            issued_at=NOW,
        )
    )
    return evidence, attestation


def test_claim_requires_verified_result_and_l3_adapter_attestation() -> None:
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="backtested-v1",
            policy_version=1,
            claim_type="backtested",
            requirements=(
                EvidenceRequirement(
                    payload_kind="result",
                    require_verified_result=True,
                    minimum_adapter_maturity="L3",
                ),
            ),
        )
    )
    l3_evidence, l3_attestation = _claim_inputs("L3")
    l2_evidence, l2_attestation = _claim_inputs("L2")
    allowed = evaluate_claim(
        policy, (l3_evidence,), (l3_attestation,), subject_ref="experiment:1", evaluated_at=NOW
    )
    denied = evaluate_claim(
        policy, (l2_evidence,), (l2_attestation,), subject_ref="experiment:1", evaluated_at=NOW
    )
    assert allowed.allowed
    assert not denied.allowed
    assert denied.reason_codes == ("QST_CLAIM_REQUIREMENT_MISSING:result",)


def test_ai4finance_maturity_matrix_matches_golden_claim_boundary() -> None:
    eligible = {name for name, cls in ADAPTER_TYPES.items() if cls.descriptor.workflow_claim_eligible}
    assert eligible == {"finrobot", "finrl", "finrl_x", "qlib"}


def test_finrobot_golden_workflow_produces_claim_evidence(tmp_path: Path) -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "ai4finance" / "finrobot.yaml"
    adapter = FinRobotEvidenceAdapter(ContentAddressedStore(tmp_path / "store"))
    descriptors = adapter.describe_artifacts(str(fixture))
    activity = seal_activity(
        ActivityRecord(
            activity_type="finrobot.agent_workflow",
            status="verified",
            output_artifact_ids=tuple(item.descriptor_id for item in descriptors),
            started_at=NOW,
            ended_at=NOW,
        )
    )
    evidence = verified_result_evidence(
        activity, descriptors, subject_ref="finrobot-golden-1", observed_at=NOW
    )
    attestation = seal_attestation(
        Attestation(
            issuer_actor_id=HASH_C,
            subject_evidence_ids=(evidence.evidence_id,),
            predicate_type="qst.adapter-verification/1.0",
            statement={
                "adapter_id": adapter.descriptor.adapter_id,
                "maturity": adapter.descriptor.maturity,
                "verified": adapter.verify(
                    seal_evidence(
                        EvidenceEnvelope(
                            subject_ref="finrobot-golden-1",
                            observed_at=NOW,
                            payload={
                                "kind": "external_record",
                                "adapter_id": adapter.descriptor.adapter_id,
                                "record_type": "workflow",
                                "record_schema": "qst-ai4finance-workflow/1.0",
                                "record": adapter.collect_run(str(fixture)),
                            },
                        )
                    )
                ),
            },
            issued_at=NOW,
        )
    )
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="experiment-completed-v1",
            policy_version=1,
            claim_type="experiment_completed",
            requirements=(
                EvidenceRequirement(
                    payload_kind="result",
                    require_verified_result=True,
                    minimum_adapter_maturity="L3",
                ),
            ),
        )
    )
    decision = evaluate_claim(
        policy, (evidence,), (attestation,), subject_ref="finrobot-golden-1", evaluated_at=NOW
    )
    assert decision.allowed


def test_receipt_layers_have_distinct_identity_material() -> None:
    experiment = seal_experiment_receipt(
        ExperimentReceipt(
            strategy_hash=HASH_A,
            data_snapshot_ids=(HASH_B,),
            evaluator_adapter_id="qst.ai4finance.finrl",
            evaluator_adapter_version="1.0.0a1",
            parameters={"window": 20},
            costs={"rate": 0.001},
            seeds=(7,),
        )
    )
    agent = seal_agent_receipt(
        AgentReceipt(
            experiment_hash=experiment.experiment_hash,
            agent_actor_id=HASH_C,
            model_id="declared-model",
            tool_versions={"qst": "1.0.0a1"},
            prompt_ref="prompt:v1",
            task_ref="task:review",
            approval_ids=(HASH_B,),
            recommendation={"decision": "review"},
        )
    )
    changed_seed = seal_experiment_receipt(
        experiment.model_copy(update={"experiment_hash": None, "seeds": (8,)})
    )
    assert experiment.experiment_hash != agent.agent_receipt_hash
    assert experiment.experiment_hash != changed_seed.experiment_hash


def test_python_sources_contain_no_nul_bytes() -> None:
    root = Path(__file__).resolve().parents[2] / "qst"
    assert [path for path in root.rglob("*.py") if b"\x00" in path.read_bytes()] == []
