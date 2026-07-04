from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from qst.attestations import Attestation, seal_attestation
from qst.claims import (
    ClaimDecision,
    ClaimPolicy,
    EvidenceRequirement,
    seal_claim_decision,
    seal_claim_policy,
)
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, seal_evidence
from qst.identity import identity_hash
from qst.provenance import (
    ActivityRecord,
    ActorDescriptor,
    ArtifactDescriptor,
    seal_activity,
    seal_actor,
    seal_artifact,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


def test_identity_domains_separate_equal_payloads() -> None:
    payload = {"value": 1}
    assert identity_hash("qst:evidence:v1", payload) != identity_hash(
        "qst:attestation:v1", payload
    )


def test_set_like_input_order_does_not_change_identity() -> None:
    left = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:42",
            observed_at=NOW,
            parent_evidence_ids=(HASH_B, HASH_A),
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="complete",
                artifact_ids=(HASH_B, HASH_A),
            ),
        )
    )
    right = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:42",
            observed_at=NOW,
            parent_evidence_ids=(HASH_A, HASH_B),
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="complete",
                artifact_ids=(HASH_A, HASH_B),
            ),
        )
    )
    assert left == right


def test_actor_artifact_and_activity_sealing_is_deterministic() -> None:
    actor = seal_actor(ActorDescriptor(kind="agent", name="FinRobot", tool_ids=("b", "a")))
    artifact = seal_artifact(
        ArtifactDescriptor(
            media_type="application/octet-stream",
            digest=HASH_A,
            size=42,
            uris=("file:///b", "file:///a"),
        )
    )
    activity = seal_activity(
        ActivityRecord(
            activity_type="external.training",
            status="verified",
            actor_ids=(actor.actor_id,),
            output_artifact_ids=(artifact.descriptor_id,),
            started_at=NOW,
            ended_at=NOW,
        )
    )
    assert actor.actor_id and artifact.descriptor_id and activity.activity_id
    assert actor.tool_ids == ("a", "b")
    assert artifact.uris == ("file:///a", "file:///b")


def test_artifact_keeps_raw_and_normalized_digests_distinct() -> None:
    descriptor = seal_artifact(
        ArtifactDescriptor(
            media_type="text/csv",
            digest=HASH_A,
            normalized_digest=HASH_B,
            normalization="qst:csv-table:v1",
            size=10,
        )
    )
    assert descriptor.digest != descriptor.normalized_digest
    with pytest.raises(ValidationError, match="declared together"):
        ArtifactDescriptor(
            media_type="text/csv", digest=HASH_A, normalized_digest=HASH_B, size=10
        )


def test_evidence_attestation_and_claim_are_separate_sealed_records() -> None:
    evidence = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:42",
            observed_at=NOW,
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="verified",
                artifact_ids=(HASH_B,),
                metrics={"sharpe": 1.2},
            ),
        )
    )
    attestation = seal_attestation(
        Attestation(
            issuer_actor_id=HASH_A,
            subject_evidence_ids=(evidence.evidence_id,),
            predicate_type="result-reviewed",
            statement={"reviewed": True},
            issued_at=NOW,
        )
    )
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="backtest-policy",
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
    decision = seal_claim_decision(
        ClaimDecision(
            claim_type="backtested",
            subject_ref="experiment:42",
            policy_hash=policy.policy_hash,
            allowed=True,
            evidence_ids=(evidence.evidence_id,),
            attestation_ids=(attestation.attestation_id,),
            reason_codes=("QST_CLAIM_REQUIREMENTS_MET",),
            evaluated_at=NOW,
        )
    )
    assert len({evidence.evidence_id, attestation.attestation_id, decision.decision_id}) == 3


def test_tampered_sealed_record_is_rejected() -> None:
    actor = seal_actor(ActorDescriptor(kind="human", name="reviewer"))
    value = actor.model_dump(mode="json")
    value["name"] = "different-reviewer"
    with pytest.raises(ValidationError, match="actor_id does not match"):
        ActorDescriptor.model_validate(value)


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        EvidenceEnvelope(
            subject_ref="experiment:42",
            observed_at=datetime(2026, 7, 4, 12, 0),
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="partial",
            ),
        )


def test_verified_activity_requires_end_time() -> None:
    with pytest.raises(ValidationError, match="requires ended_at"):
        ActivityRecord(activity_type="external.run", status="verified", started_at=NOW)


def test_models_reject_cross_layer_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        EvidenceEnvelope.model_validate(
            {
                "subject_ref": "experiment:42",
                "observed_at": NOW.isoformat(),
                "allowed": True,
                "payload": {
                    "kind": "result",
                    "activity_id": HASH_A,
                    "collection_status": "partial",
                },
            }
        )
