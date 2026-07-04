"""Compact read-only QST tools intended for FinRobot agents."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

from qst.evidence import EvidenceEnvelope, evidence_identity
from qst.hash import compute_hashes_v2
from qst.ir import canonical_bytes_v04, load_ir_v04_file, validate_ir_v04
from qst.provenance import ArtifactDescriptor
from qst.resolver import TokenGapResolver, vocabulary_snapshot
from qst.storage import ContentAddressedStore
from qst.tokens import TokenRegistryV2, builtin_token_packs


class FinRobotReadOnlyTools:
    """Six bounded tools with no model, backtest, custom-code, or trading execution."""

    def __init__(self, store: ContentAddressedStore) -> None:
        self.store = store
        registry = TokenRegistryV2.from_packs(builtin_token_packs())
        self.resolver = TokenGapResolver(vocabulary_snapshot(registry))

    def strategy_validate(self, strategy: Path) -> dict[str, Any]:
        result = validate_ir_v04(load_ir_v04_file(strategy))
        return {
            "ok": result.ok,
            "diagnostic_count": len(result.diagnostics),
            "diagnostics": [item.model_dump(mode="json") for item in result.diagnostics],
        }

    def strategy_identity(self, strategy: Path) -> dict[str, Any]:
        ir = load_ir_v04_file(strategy)
        canonical = canonical_bytes_v04(ir)
        hashes = compute_hashes_v2(ir)
        return {
            **hashes.__dict__,
            "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
            "canonical_size": len(canonical),
        }

    def token_resolve(self, intent: dict[str, Any]) -> dict[str, Any]:
        result = self.resolver.resolve(intent)
        return {
            "route": result.route,
            "resolution_hash": result.identity.resolution_hash,
            "candidate_count": len(result.candidates),
            "top_candidate": result.candidates[0].token_id if result.candidates else None,
            "issue_codes": [item.code for item in result.issues],
        }

    def evidence_inspect(self, evidence: EvidenceEnvelope) -> dict[str, Any]:
        return {
            "sealed": evidence.evidence_id == evidence_identity(evidence),
            "evidence_id": evidence.evidence_id,
            "subject_ref": evidence.subject_ref,
            "payload_kind": evidence.payload.kind,
            "parent_count": len(evidence.parent_evidence_ids),
        }

    def artifact_verify(self, descriptor: ArtifactDescriptor) -> dict[str, Any]:
        return {
            "descriptor_id": descriptor.descriptor_id,
            "digest": descriptor.digest,
            "valid": self.store.verify(descriptor),
        }

    def claim_readiness(self, evidence: tuple[EvidenceEnvelope, ...]) -> dict[str, Any]:
        kinds = Counter(item.payload.kind for item in evidence)
        return {
            "evidence_count": len(evidence),
            "sealed_count": sum(
                item.evidence_id == evidence_identity(item) for item in evidence
            ),
            "payload_counts": dict(sorted(kinds.items())),
            "claim_decision": "not_evaluated",
        }

