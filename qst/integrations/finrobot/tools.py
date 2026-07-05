"""Bounded, read-only QST tools intended for FinRobot agents."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from qst.admission import admit_backtested_claim, admit_strategy_memory
from qst.evidence import EvidenceEnvelope, evidence_identity
from qst.hash import compute_hashes_v2
from qst.ir import canonical_bytes_v04, load_ir_v04, validate_ir_v04
from qst.provenance import ArtifactDescriptor
from qst.receipts import (
    ExperimentReceipt,
    StrategyRecordReceipt,
    build_strategy_record_receipt,
)
from qst.resolver import TokenGapResolver, vocabulary_snapshot
from qst.storage import ContentAddressedStore
from qst.tokens import TokenRegistryV2, builtin_token_packs

MAX_STRATEGY_BYTES = 1024 * 1024
INLINE_CANONICAL_BYTES = 256 * 1024


class FinRobotReadOnlyTools:
    """QST inspection tools with no model, backtest, custom-code, or trading execution."""

    def __init__(self, store: ContentAddressedStore) -> None:
        self.store = store
        registry = TokenRegistryV2.from_packs(builtin_token_packs())
        self.registry = registry
        self.resolver = TokenGapResolver(vocabulary_snapshot(registry))
        self._builtin_refs = {record.spec.ref_key for record in registry.records}

    def strategy_validate(self, strategy: Path | str) -> dict[str, Any]:
        """Validate a bounded GKR path or YAML/JSON text without executing it."""

        try:
            ir = self._load_strategy(strategy)
        except (OSError, ValueError, ValidationError) as exc:
            return {
                "ok": False,
                "diagnostic_count": 1,
                "diagnostics": [self._diagnostic("invalid_strategy_record", str(exc), "error")],
            }
        result = validate_ir_v04(ir)
        diagnostics = [item.model_dump(mode="json") for item in result.diagnostics]
        diagnostics.extend(self._agent_diagnostics(ir))
        diagnostics.sort(key=lambda item: (item["code"], item.get("message", "")))
        return {
            "ok": result.ok and not any(item["severity"] == "error" for item in diagnostics),
            "diagnostic_count": len(diagnostics),
            "diagnostics": diagnostics,
        }

    def strategy_identity(self, strategy: Path | str) -> dict[str, Any]:
        """Return canonical strategy identity and bounded canonical delivery."""

        ir = self._load_strategy(strategy)
        canonical = canonical_bytes_v04(ir)
        hashes = compute_hashes_v2(ir)
        receipt = build_strategy_record_receipt(
            ir,
            non_goals=(
                "no broker or exchange execution",
                "no backtest or profitability claim",
                "no live trading runtime",
            ),
        )
        return {
            **hashes.__dict__,
            "strategy_hash": receipt.strategy_hash,
            "strategy_receipt_id": receipt.strategy_receipt_id,
            "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
            "canonical_size": len(canonical),
            "canonical": self._deliver_canonical(canonical),
        }

    def strategy_record(
        self, strategy: Path | str, *, non_goals: tuple[str, ...]
    ) -> StrategyRecordReceipt:
        """Create a sealed strategy-memory receipt; this performs no admission side effect."""

        return build_strategy_record_receipt(self._load_strategy(strategy), non_goals=non_goals)

    def strategy_memory_admission(self, receipt: StrategyRecordReceipt) -> dict[str, Any]:
        """Evaluate strategy-memory admission without writing agent memory."""

        return admit_strategy_memory(receipt).model_dump(mode="json")

    def backtest_admission(
        self, receipt: ExperimentReceipt, evidence: tuple[EvidenceEnvelope, ...]
    ) -> dict[str, Any]:
        """Evaluate a backtested label without running a backtest."""

        return admit_backtested_claim(receipt, evidence).model_dump(mode="json")

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

    def _load_strategy(self, strategy: Path | str) -> Any:
        if isinstance(strategy, Path):
            text = self._read_bounded_path(strategy)
        elif "\n" in strategy or strategy.lstrip().startswith(("{", "schema_version:")):
            text = strategy
        else:
            candidate = Path(strategy)
            text = self._read_bounded_path(candidate) if candidate.is_file() else strategy
        if len(text.encode("utf-8")) > MAX_STRATEGY_BYTES:
            raise ValueError("strategy input exceeds 1 MiB")
        return load_ir_v04(text)

    @staticmethod
    def _read_bounded_path(path: Path) -> str:
        resolved = path.resolve(strict=True)
        if resolved.stat().st_size > MAX_STRATEGY_BYTES:
            raise ValueError("strategy input exceeds 1 MiB")
        return resolved.read_text(encoding="utf-8")

    def _deliver_canonical(self, canonical: bytes) -> dict[str, Any]:
        if len(canonical) <= INLINE_CANONICAL_BYTES:
            return {
                "delivery": "inline",
                "media_type": "application/vnd.qst.canonical+json",
                "value": json.loads(canonical.decode("utf-8")),
            }
        descriptor = self.store.put_bytes(
            canonical, media_type="application/vnd.qst.canonical+json"
        )
        return {
            "delivery": "content_addressed_store",
            "descriptor": descriptor.model_dump(mode="json"),
        }

    def _agent_diagnostics(self, ir: Any) -> list[dict[str, str]]:
        diagnostics: list[dict[str, str]] = []
        for node in ir.strategy.nodes:
            if node.token_ref is None:
                continue
            ref = node.token_ref
            key = (ref.namespace, ref.name, ref.version, ref.behavior_version)
            if key in self._builtin_refs:
                continue
            if ref.namespace == "custom" or "custom_token_runtime" in ir.capabilities:
                diagnostics.append(
                    self._diagnostic(
                        "custom_token_requires_approval",
                        f"Node {node.id} references a custom token.",
                        "error",
                    )
                )
            else:
                diagnostics.append(
                    self._diagnostic(
                        "unsupported_token",
                        f"Node {node.id} references an unknown token.",
                        "error",
                    )
                )
        if "data_binding" not in ir.metadata:
            diagnostics.append(
                self._diagnostic(
                    "missing_data_binding",
                    "Strategy metadata does not bind an external data snapshot.",
                    "warning",
                )
            )
        if not any(
            node.token_ref is not None and node.token_ref.namespace in {"risk", "gate"}
            for node in ir.strategy.nodes
        ):
            diagnostics.append(
                self._diagnostic(
                    "missing_risk_constraint",
                    "No explicit risk or gate record is present.",
                    "warning",
                )
            )
        diagnostics.append(
            self._diagnostic(
                "not_executable_by_adapter",
                "The FinRobot bridge validates records and does not execute strategies.",
                "warning",
            )
        )
        return diagnostics

    @staticmethod
    def _diagnostic(code: str, message: str, severity: str) -> dict[str, str]:
        return {"code": code, "message": message, "severity": severity}


def finrobot_toolkit_config(tools: FinRobotReadOnlyTools) -> tuple[Callable[..., Any], ...]:
    """Return callables accepted by FinRobot's callable toolkit registration path."""

    return (
        tools.strategy_validate,
        tools.strategy_identity,
        tools.token_resolve,
        tools.evidence_inspect,
        tools.artifact_verify,
        tools.claim_readiness,
    )
