from __future__ import annotations

from typing import cast

from quant_strategy_tokenizer.core.output import normalize_token_output
from quant_strategy_tokenizer.tokens.registry import get_registry


def _reduce(decisions: list[dict[str, object]], **params: object) -> dict[str, object]:
    registered = get_registry().get("decision.reduce", 2)
    output = normalize_token_output(registered.executor(decisions=decisions, **params))
    return cast(dict[str, object], output.values["decision"].model_dump(mode="json", exclude_none=True))


def test_error_short_circuits_all() -> None:
    result = _reduce(
        [
            {"kind": "accept", "reason": "a"},
            {"kind": "error", "exception_kind": "boom", "message": "bad"},
            {"kind": "block", "reason": "cap", "severity": "critical"},
        ]
    )

    assert result["kind"] == "error"
    assert result["exception_kind"] == "boom"


def test_block_higher_than_unknown() -> None:
    result = _reduce(
        [
            {"kind": "block", "reason": "cap", "severity": "critical"},
            {"kind": "unknown", "missing_info_kind": "dependency_unknown"},
            {"kind": "accept", "reason": "a"},
        ]
    )

    assert result["kind"] == "block"
    assert result["severity"] == "critical"


def test_multiple_blocks_take_highest_severity() -> None:
    result = _reduce(
        [
            {"kind": "block", "reason": "warn", "severity": "warning", "evidence": {"a": 1}},
            {"kind": "block", "reason": "crit", "severity": "critical", "evidence": {"b": 2}},
        ]
    )

    assert result["kind"] == "block"
    assert result["severity"] == "critical"
    assert result["evidence"] == {"a": 1, "b": 2}


def test_block_demoted_to_reject_with_policy() -> None:
    result = _reduce(
        [
            {"kind": "accept", "reason": "a"},
            {"kind": "block", "reason": "cap", "severity": "critical"},
        ],
        block_handling="treat_as_reject",
        policy="all_accept",
    )

    assert result == {"kind": "reject", "reason": "block_demoted: cap", "evidence": {}}


def test_abstain_skip_with_remaining_accept() -> None:
    result = _reduce(
        [
            {"kind": "accept", "reason": "a"},
            {"kind": "abstain", "reason": "not_applicable"},
            {"kind": "reject", "reason": "b"},
        ],
        abstain_handling="skip",
        policy="any_accept",
    )

    assert result["kind"] == "accept"
    assert result["reason"] == "any_accept"


def test_all_abstain_skip_fallback() -> None:
    result = _reduce(
        [
            {"kind": "abstain", "reason": "x"},
            {"kind": "abstain", "reason": "y"},
        ],
        abstain_handling="skip",
    )

    assert result["kind"] == "unknown"
    assert result["reason"] == "all_abstain"


def test_unknown_treat_as_reject_with_accept() -> None:
    result = _reduce(
        [
            {"kind": "accept", "reason": "a"},
            {"kind": "unknown", "missing_info_kind": "dependency_unknown"},
        ],
        unknown_handling="treat_as_reject",
        policy="all_accept",
    )

    assert result["kind"] == "reject"
    assert result["reason"] == "unknown_treated_as_reject"
