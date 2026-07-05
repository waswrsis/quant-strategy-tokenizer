from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FINAL_DOCS = [
    "docs/FINAL_SCOPE.md",
    "docs/FINAL_ACCEPTANCE.md",
    "docs/FINAL_REPORT.md",
    "docs/ROADMAP_CLOSED.md",
    "docs/NON_GOALS.md",
    "docs/FINAL_HANDOFF.md",
]

AGENT_DOCS = [
    "docs/agent/AGENT_TAKEOVER_PROMPT.md",
    "docs/agent/AGENT_PLAYBOOK.md",
    "docs/agent/USAGE_GUIDE.md",
    "docs/agent/TOKEN_REGISTRATION_GUIDE.md",
    "docs/agent/RECIPE_AUTHORING_GUIDE.md",
    "docs/agent/CUSTOM_TOKEN_GUIDE.md",
    "docs/agent/SECONDARY_DEVELOPMENT_GUIDE.md",
    "docs/agent/RECORD_LAYER_WORKFLOW.md",
    "docs/agent/QST_1_0_AGENT_PROMPT.md",
]

ADAPTER_DOCS = [
    "docs/adapters/README.md",
    "docs/adapters/QLIB_ADAPTER_BOUNDARY.md",
    "docs/adapters/QLIB_ADAPTER_GUIDE.md",
]

CLOSURE_DOCS = FINAL_DOCS + AGENT_DOCS + ADAPTER_DOCS

FORBIDDEN_STALE_CLAIMS = [
    "quant_strategy_tokenizer",
    ".qst.yaml",
    "qst execute",
    "qst promote",
    "qst compare",
    "qst adapter freqtrade import",
    "freqtrade adapter proof",
]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_final_closure_docs_exist_and_are_non_empty() -> None:
    for relative in CLOSURE_DOCS:
        path = ROOT / relative
        assert path.exists(), relative
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# "), relative
        assert len(text.split()) >= 20, relative


def test_readme_declares_alpha_and_v04_compatibility_status() -> None:
    readme = _read("README.md")
    assert "archived agent-ready research prototype" in readme
    assert "1.0.0a2" in readme
    assert "strategy identity, evidence, and governance" in readme
    assert "Final Handoff" in readme
    assert "docs/FINAL_HANDOFF.md" in readme
    assert "docs/agent/AGENT_TAKEOVER_PROMPT.md" in readme
    assert "Qlib Compatibility Import" in readme
    assert "qst.cli adapter qlib import" in readme


def test_closure_docs_do_not_claim_stale_package_or_missing_broad_cli() -> None:
    for relative in CLOSURE_DOCS:
        text = _read(relative)
        lowered = text.lower()
        for forbidden in FORBIDDEN_STALE_CLAIMS:
            assert forbidden not in lowered, f"{relative} contains stale claim {forbidden!r}"


def test_adapter_docs_mark_qlib_partial_non_lossless_boundary() -> None:
    joined = "\n".join(_read(relative).lower() for relative in ADAPTER_DOCS)
    for required in [
        "qlib",
        "partial",
        "lossless",
        "broker",
        "exchange",
        "live execution",
        "qrun",
        "model training",
        "backtest",
    ]:
        assert required in joined
    assert "not lossless" in joined or "must not claim lossless" in joined
    assert "qst adapter qlib import" in joined


def test_agent_readme_links_final_handoff_guides_without_replacing_prompt_pack() -> None:
    text = _read("docs/agent/README.md")
    assert "prompts/qst_stage_3c_v0_3_2/README.md" in text
    for relative in [
        "AGENT_TAKEOVER_PROMPT.md",
        "AGENT_PLAYBOOK.md",
        "USAGE_GUIDE.md",
        "TOKEN_REGISTRATION_GUIDE.md",
        "RECORD_LAYER_WORKFLOW.md",
        "QST_1_0_AGENT_PROMPT.md",
    ]:
        assert relative in text


def test_qlib_command_remains_documented_in_compatibility_usage() -> None:
    for relative in [
        "docs/agent/USAGE_GUIDE.md",
        "docs/adapters/QLIB_ADAPTER_GUIDE.md",
    ]:
        text = _read(relative)
        assert "qst.cli adapter qlib import" in text


def test_v04_executor_is_only_documented_under_compatibility_namespace() -> None:
    for relative in CLOSURE_DOCS:
        text = _read(relative)
        if "token execute" in text:
            assert "compat-v04 token execute" in text


def test_no_freqtrade_adapter_docs_remain() -> None:
    assert not (ROOT / "docs" / "adapters" / "FREQTRADE_ADAPTER_BOUNDARY.md").exists()
    assert not (ROOT / "docs" / "adapters" / "FREQTRADE_ADAPTER_GUIDE.md").exists()


def test_record_layer_agent_guidance_has_current_admission_boundaries() -> None:
    joined = "\n".join(
        _read(relative)
        for relative in [
            "docs/agent/RECORD_LAYER_WORKFLOW.md",
            "docs/agent/USAGE_GUIDE.md",
            "docs/agent/AGENT_PLAYBOOK.md",
        ]
    )
    for required in [
        "StrategyRecordReceipt",
        "ExperimentReceipt 2.0",
        "AgentReceipt 2.0",
        "backtested",
        "record_only",
        "advisory",
        "enforce",
        "not_executable_by_adapter",
        "human review",
    ]:
        assert required in joined


def test_claude_project_memory_is_concise_and_points_to_canonical_guidance() -> None:
    text = _read("CLAUDE.md")
    assert text.startswith("# QST Project Instructions")
    assert len(text.splitlines()) < 100
    assert "docs/agent/QST_1_0_AGENT_PROMPT.md" in text
    assert "docs/agent/RECORD_LAYER_WORKFLOW.md" in text
    assert "Evidence is not approval" in text
    assert "Do not commit, push, tag" in text


def test_qst_1_agent_prompt_is_operational_but_compact() -> None:
    text = _read("docs/agent/QST_1_0_AGENT_PROMPT.md")
    assert len(text.splitlines()) < 180
    for required in [
        "git status --short",
        "StrategyRecordReceipt",
        "ExperimentReceipt 2.0",
        "AgentReceipt 2.0",
        "record_only",
        "advisory",
        "enforce",
        "Explicit Permission Required",
        "Stop Conditions",
        "Commit/push/tag status",
        "qst.cli inspect",
    ]:
        assert required in text


def test_agent_facing_prompts_use_english_only() -> None:
    paths = [ROOT / "CLAUDE.md", ROOT / "docs" / "agent" / "QST_1_0_AGENT_PROMPT.md"]
    paths.extend(
        (ROOT / "docs" / "agent" / "prompts" / "qst_stage_3c_v0_3_2").rglob("*.md")
    )
    for path in paths:
        assert not re.search(r"[\u3400-\u9fff]", path.read_text(encoding="utf-8")), path
