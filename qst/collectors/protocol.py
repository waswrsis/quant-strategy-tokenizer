"""Read-only evidence adapter and collector state protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, seal_evidence
from qst.provenance import ActivityRecord, ArtifactDescriptor, seal_activity

ALLOWED_TRANSITIONS = {
    "discovered": {"collecting", "failed"},
    "collecting": {"partial", "complete", "failed"},
    "partial": {"collecting", "complete", "failed"},
    "complete": {"verified", "failed"},
    "verified": set(),
    "failed": set(),
}


@runtime_checkable
class EvidenceAdapter(Protocol):
    """Adapters discover and collect evidence but never execute external work."""

    def probe(self, source: str) -> dict[str, Any]: ...

    def discover(self, source: str) -> dict[str, Any]: ...

    def extract_plan(self, source: str) -> dict[str, Any]: ...

    def collect_run(self, run_ref: str) -> dict[str, Any]: ...

    def describe_artifacts(self, run_ref: str) -> tuple[ArtifactDescriptor, ...]: ...

    def verify(self, evidence: EvidenceEnvelope) -> bool: ...


def transition_activity(
    current: ActivityRecord,
    status: str,
    *,
    at: datetime,
    output_artifact_ids: tuple[str, ...] | None = None,
) -> ActivityRecord:
    """Create a sealed immutable activity snapshot after validating the transition."""

    if current.activity_id is None:
        raise ValueError("current activity must be sealed")
    if status not in ALLOWED_TRANSITIONS[current.status]:
        raise ValueError(f"invalid activity transition {current.status} -> {status}")
    outputs = current.output_artifact_ids if output_artifact_ids is None else output_artifact_ids
    if status == "verified" and not outputs:
        raise ValueError("verified activity requires stable output artifacts")
    ended_at = at if status in {"complete", "verified", "failed"} else None
    return seal_activity(
        ActivityRecord(
            activity_type=current.activity_type,
            status=status,  # type: ignore[arg-type]
            actor_ids=current.actor_ids,
            input_artifact_ids=current.input_artifact_ids,
            output_artifact_ids=outputs,
            previous_activity_id=current.activity_id,
            external_run_ref=current.external_run_ref,
            started_at=current.started_at,
            ended_at=ended_at,
            attributes=current.attributes,
        )
    )


def verified_result_evidence(
    activity: ActivityRecord,
    artifacts: tuple[ArtifactDescriptor, ...],
    *,
    subject_ref: str,
    observed_at: datetime,
) -> EvidenceEnvelope:
    """Emit verified result evidence only for a stable verified artifact set."""

    if activity.status != "verified" or activity.activity_id is None:
        raise ValueError("result activity must be sealed and verified")
    descriptor_ids = tuple(item.descriptor_id for item in artifacts)
    if any(item is None for item in descriptor_ids):
        raise ValueError("all artifact descriptors must be sealed")
    expected = tuple(sorted(activity.output_artifact_ids))
    actual = tuple(sorted(item for item in descriptor_ids if item is not None))
    if actual != expected:
        raise ValueError("verified artifact set does not match activity outputs")
    return seal_evidence(
        EvidenceEnvelope(
            subject_ref=subject_ref,
            observed_at=observed_at,
            source_activity_id=activity.activity_id,
            payload=ResultEvidencePayload(
                activity_id=activity.activity_id,
                collection_status="verified",
                artifact_ids=actual,
            ),
        )
    )

