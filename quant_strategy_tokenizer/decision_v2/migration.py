"""Legacy decision.reduce migration classification for WP7."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.validation_v2 import Diagnostic, ValidationResult

LegacyDecisionKind = Literal[
    "accept",
    "reject",
    "unknown",
    "abstain",
    "block",
    "error",
]


class LegacyDecisionMapping(BaseModel):
    """Mapping from a P1 Decision variant to a v0.4 DecisionKind or diagnostic."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    legacy_kind: LegacyDecisionKind
    v04_kind: Literal["accept", "reject", "unknown", "block"] | None
    diagnostic_code: str | None = None


class LegacyReduceMigration(BaseModel):
    """Migration classification for legacy decision.reduce policies."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    legacy_policy: str
    legacy_unknown_handling: str
    target_kind: Literal["fold_policy", "diagnostic"]
    target_id: str | None = None
    result: ValidationResult


def map_legacy_decision_kind(kind: LegacyDecisionKind) -> LegacyDecisionMapping:
    """Map one P1 Decision variant into v0.4 Decision Algebra material."""

    if kind == "abstain":
        return LegacyDecisionMapping(legacy_kind=kind, v04_kind="unknown")
    if kind == "error":
        return LegacyDecisionMapping(
            legacy_kind=kind,
            v04_kind=None,
            diagnostic_code="QST_V2_DECISION_LEGACY_ERROR_DIAGNOSTIC_ONLY",
        )
    return LegacyDecisionMapping(legacy_kind=kind, v04_kind=kind)


def classify_legacy_decision_reduce(
    *,
    policy: str,
    unknown_handling: str,
    block_handling: str = "forward",
    abstain_handling: str = "skip",
    error_handling: str = "keep_as_diagnostic",
) -> LegacyReduceMigration:
    """Classify whether a legacy decision.reduce policy maps exactly to WP7."""

    if block_handling != "forward":
        return _non_migratable(
            policy,
            unknown_handling,
            "QST_V2_DECISION_BLOCK_HANDLING_NON_MIGRATABLE",
            "Only block_handling='forward' maps to v0.4 block semantics.",
        )
    if abstain_handling not in {"skip", "treat_as_unknown"}:
        return _non_migratable(
            policy,
            unknown_handling,
            "QST_V2_DECISION_ABSTAIN_HANDLING_NON_MIGRATABLE",
            "Legacy abstain must map to v0.4 unknown.",
        )
    if error_handling != "keep_as_diagnostic":
        return _non_migratable(
            policy,
            unknown_handling,
            "QST_V2_DECISION_ERROR_HANDLING_NON_MIGRATABLE",
            "Legacy error cannot be silently migrated into a DecisionKind.",
        )

    target_id: str | None = None
    if policy == "all_accept" and unknown_handling == "treat_as_reject":
        target_id = "decision.strict_and"
    elif policy == "all_accept" and unknown_handling == "treat_as_accept":
        target_id = "decision.permissive_and"
    elif policy == "all_accept" and unknown_handling in {
        "propagate_unknown",
        "treat_as_unknown",
    }:
        target_id = "decision.unknown_propagating_and"
    elif policy == "any_accept" and unknown_handling in {
        "propagate_unknown",
        "treat_as_unknown",
    }:
        target_id = "decision.any_accept"

    if target_id is None:
        return _non_migratable(
            policy,
            unknown_handling,
            "QST_V2_DECISION_REDUCE_POLICY_NON_MIGRATABLE",
            "Legacy decision.reduce policy is ambiguous under v0.4 Decision Algebra.",
        )

    return LegacyReduceMigration(
        legacy_policy=policy,
        legacy_unknown_handling=unknown_handling,
        target_kind="fold_policy",
        target_id=target_id,
        result=ValidationResult(),
    )


def _non_migratable(
    policy: str,
    unknown_handling: str,
    code: str,
    message: str,
) -> LegacyReduceMigration:
    return LegacyReduceMigration(
        legacy_policy=policy,
        legacy_unknown_handling=unknown_handling,
        target_kind="diagnostic",
        result=ValidationResult(
            diagnostics=[
                Diagnostic(
                    code=code,
                    severity="error",
                    phase="schema",
                    message=message,
                )
            ]
        ),
    )
