"""Deterministic evidence-based claim policy evaluation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from qst.attestations import Attestation, attestation_identity
from qst.claims.models import (
    ClaimDecision,
    ClaimPolicy,
    claim_policy_identity,
    seal_claim_decision,
)
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, evidence_identity
from qst.provenance import normalize_utc

MATURITY_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


def evaluate_claim(
    policy: ClaimPolicy,
    evidence: tuple[EvidenceEnvelope, ...],
    attestations: tuple[Attestation, ...],
    *,
    subject_ref: str,
    evaluated_at: datetime,
) -> ClaimDecision:
    """Evaluate requirements without treating evidence or attestations as self-approval."""

    if policy.policy_hash is None:
        raise ValueError("claim policy must be sealed")
    if policy.policy_hash != claim_policy_identity(policy):
        raise ValueError("policy_hash does not match policy material")
    evaluated_at = normalize_utc(evaluated_at)
    evidence_by_id = {
        item.evidence_id: item
        for item in evidence
        if item.evidence_id is not None
        and item.evidence_id == evidence_identity(item)
        and item.subject_ref == subject_ref
        and item.observed_at <= evaluated_at
    }
    valid_evidence = tuple(
        evidence_by_id[evidence_id] for evidence_id in sorted(evidence_by_id)
    )
    by_kind: dict[str, list[EvidenceEnvelope]] = defaultdict(list)
    for item in valid_evidence:
        by_kind[item.payload.kind].append(item)
    maturity_by_evidence, valid_attestation_ids = _adapter_maturities(
        attestations, evidence_by_id, evaluated_at=evaluated_at
    )
    reasons: list[str] = []
    allowed = True
    for requirement in policy.requirements:
        candidates = by_kind.get(requirement.payload_kind, [])
        qualifying = []
        for item in candidates:
            if requirement.require_verified_result:
                if not isinstance(item.payload, ResultEvidencePayload):
                    continue
                if item.payload.collection_status != "verified":
                    continue
            maturity = maturity_by_evidence.get(item.evidence_id or "", "L0")
            if MATURITY_RANK[maturity] < MATURITY_RANK[requirement.minimum_adapter_maturity]:
                continue
            qualifying.append(item)
        if len(qualifying) < requirement.minimum_count:
            allowed = False
            reasons.append(f"QST_CLAIM_REQUIREMENT_MISSING:{requirement.payload_kind}")
    if allowed:
        reasons.append("QST_CLAIM_REQUIREMENTS_MET")
    return seal_claim_decision(
        ClaimDecision(
            claim_type=policy.claim_type,
            subject_ref=subject_ref,
            policy_hash=policy.policy_hash,
            allowed=allowed,
            evidence_ids=tuple(item.evidence_id for item in valid_evidence if item.evidence_id),
            attestation_ids=valid_attestation_ids,
            reason_codes=tuple(reasons),
            evaluated_at=evaluated_at,
        )
    )


def _adapter_maturities(
    attestations: tuple[Attestation, ...],
    evidence_by_id: dict[str, EvidenceEnvelope],
    *,
    evaluated_at: datetime,
) -> tuple[dict[str, str], tuple[str, ...]]:
    result: dict[str, str] = {}
    valid_attestation_ids: set[str] = set()
    for item in attestations:
        if item.attestation_id is None or item.attestation_id != attestation_identity(item):
            continue
        if item.predicate_type != "qst.adapter-verification/1.0":
            continue
        maturity = item.statement.get("maturity")
        verified = item.statement.get("verified")
        adapter_id = item.statement.get("adapter_id")
        if (
            maturity not in MATURITY_RANK
            or verified is not True
            or not isinstance(adapter_id, str)
            or not adapter_id
            or item.issued_at > evaluated_at
            or (maturity == "L4" and item.signature_artifact_id is None)
        ):
            continue
        relevant_ids = {
            evidence_id
            for evidence_id in item.subject_evidence_ids
            if evidence_id in evidence_by_id
            and item.issued_at >= evidence_by_id[evidence_id].observed_at
        }
        if not relevant_ids:
            continue
        valid_attestation_ids.add(item.attestation_id)
        for evidence_id in relevant_ids:
            current = result.get(evidence_id, "L0")
            if MATURITY_RANK[maturity] > MATURITY_RANK[current]:
                result[evidence_id] = maturity
    return result, tuple(sorted(valid_attestation_ids))
