from __future__ import annotations

from pathlib import Path

from tools.validate_prompt_set import validate_prompt_set

ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = ROOT / "docs" / "agent" / "prompts" / "qst_stage_3c_v0_3_2"


def _text(relative_path: str) -> str:
    return (PROMPT_ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_prompt_validator_enforces_semantic_anchors() -> None:
    result = validate_prompt_set(PROMPT_ROOT)
    checks = result["prompt_validation"]["checks"]
    semantic = next(check for check in checks if check["id"] == "semantic_anchors")

    assert semantic["result"] == "pass"


def test_repo_context_protocol_has_operational_commands() -> None:
    text = _text("core/01_REPO_CONTEXT_PROTOCOL.md")

    for anchor in (
        "git status",
        "git rev-parse",
        "pyproject.toml",
        "qst vocabulary",
        "qst validate",
        "qst hash",
        "canonicalize",
        "examples/strategies",
        "tests/reference",
        "repo_context",
    ):
        assert anchor in text


def test_classify_intent_has_boundary_rules() -> None:
    text = _text("tasks/CLASSIFY_STRATEGY_INTENT.md")

    for anchor in (
        "supported",
        "partially_supported",
        "custom_token_required",
        "reserved",
        "non_goal",
        "broker",
        "exchange",
        "live execution",
        "eventstream",
    ):
        assert anchor in text


def test_select_tokens_has_selection_output_fields() -> None:
    text = _text("tasks/SELECT_TOKENS.md")

    for anchor in (
        "selected_token_ref",
        "maturity",
        "execution_support",
        "profile_status",
        "rejected_candidates",
        "missing_tokens",
    ):
        assert anchor in text


def test_author_gkr_has_validate_hash_canonical_flow() -> None:
    text = _text("tasks/AUTHOR_GKR_STRATEGY.md")

    for anchor in (
        ".gkr.yaml",
        "node_plan",
        "qst validate",
        "qst hash",
        "canonicalize",
        "repair_gkr_diagnostics",
    ):
        assert anchor in text


def test_repair_diagnostics_has_classes_and_attempt_limit() -> None:
    text = _text("tasks/REPAIR_GKR_DIAGNOSTICS.md")

    for anchor in (
        "schema_error",
        "unknown_token",
        "port_error",
        "type_error",
        "temporal_error",
        "3 attempts",
    ):
        assert anchor in text


def test_custom_token_routing_preserves_boundary_terms() -> None:
    text = _text("tasks/CUSTOM_TOKEN_ROUTING.md")

    for anchor in (
        "verify",
        "approve",
        "grant",
        "execute",
        "must not execute",
        "do not import",
    ):
        assert anchor in text
