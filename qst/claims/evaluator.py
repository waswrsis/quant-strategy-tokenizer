"""Deterministic evidence-based claim policy evaluation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from qst.attestations import Attestation
from qst.claims.models import ClaimDecision, ClaimPolicy, seal_claim_decision
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, evidence_identity

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
    valid_evidence = tuple(
        item
        for item in evidence
        if item.evidence_id is not None and item.evidence_id == evidence_identity(item)
    )
    by_kind: dict[str, list[EvidenceEnvelope]] = defaultdict(list)
    for item in valid_evidence:
        by_kind[item.payload.kind].append(item)
    maturity_by_evidence = _adapter_maturities(attestations)
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
            attestation_ids=tuple(
                item.attestation_id for item in attestations if item.attestation_id is not None
            ),
            reason_codes=tuple(reasons),
            evaluated_at=evaluated_at,
        )
    )


def _adapter_maturities(attestations: tuple[Attestation, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in attestations:
        if item.predicate_type != "qst.adapter-verification/1.0":
            continue
        maturity = item.statement.get("maturity")
        verified = item.statement.get("verified")
        if maturity not in MATURITY_RANK or verified is not True:
            continue
        for evidence_id in item.subject_evidence_ids:
            current = result.get(evidence_id, "L0")
            if MATURITY_RANK[maturity] > MATURITY_RANK[current]:
                result[evidence_id] = maturity
    return result

