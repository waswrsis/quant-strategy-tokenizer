from __future__ import annotations

from quant_strategy_tokenizer.decision_v2 import (
    classify_legacy_decision_reduce,
    map_legacy_decision_kind,
)


def test_legacy_decision_kind_mapping() -> None:
    assert map_legacy_decision_kind("accept").v04_kind == "accept"
    assert map_legacy_decision_kind("reject").v04_kind == "reject"
    assert map_legacy_decision_kind("unknown").v04_kind == "unknown"
    assert map_legacy_decision_kind("abstain").v04_kind == "unknown"
    assert map_legacy_decision_kind("block").v04_kind == "block"

    error = map_legacy_decision_kind("error")
    assert error.v04_kind is None
    assert error.diagnostic_code == "QST_V2_DECISION_LEGACY_ERROR_DIAGNOSTIC_ONLY"


def test_legacy_reduce_supported_mappings() -> None:
    assert (
        classify_legacy_decision_reduce(
            policy="all_accept",
            unknown_handling="treat_as_reject",
        ).target_id
        == "decision.strict_and"
    )
    assert (
        classify_legacy_decision_reduce(
            policy="all_accept",
            unknown_handling="treat_as_accept",
        ).target_id
        == "decision.permissive_and"
    )
    assert (
        classify_legacy_decision_reduce(
            policy="all_accept",
            unknown_handling="propagate_unknown",
        ).target_id
        == "decision.unknown_propagating_and"
    )
    assert (
        classify_legacy_decision_reduce(
            policy="any_accept",
            unknown_handling="propagate_unknown",
        ).target_id
        == "decision.any_accept"
    )


def test_legacy_reduce_non_migratable_cases_are_diagnostics() -> None:
    ambiguous = classify_legacy_decision_reduce(
        policy="any_accept",
        unknown_handling="treat_as_accept",
    )
    error_policy = classify_legacy_decision_reduce(
        policy="all_accept",
        unknown_handling="treat_as_reject",
        error_handling="error_as_block",
    )

    assert not ambiguous.result.ok
    assert ambiguous.target_kind == "diagnostic"
    assert ambiguous.result.errors[0].code == "QST_V2_DECISION_REDUCE_POLICY_NON_MIGRATABLE"
    assert not error_policy.result.ok
    assert error_policy.result.errors[0].code == "QST_V2_DECISION_ERROR_HANDLING_NON_MIGRATABLE"
