from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from tests.ir.validator_helpers import empty_recipe_registry, make_policy_registry, make_token

runner = CliRunner()

FUTURE_DATA_STRATEGY = """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: future_data_case
strategy_version: 1
form: surface
externals:
  state:
    type: State
    required: true
  sizing:
    type: Number
    required: true
recipes: []
graph:
  - id: signal
    token: test.signal
    v: 1
    inputs: {}
  - id: risk
    token: risk.position_cap
    v: 1
    params:
      max_position: 1
      symbol_key: current_symbol
    inputs:
      decision: signal.decision
      state: state
  - id: plan
    token: plan.order_intent
    v: 1
    params:
      side: long
    inputs:
      decision: risk.decision
      sizing: sizing
outputs:
  plan: plan
"""


def _patch_policy_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = make_policy_registry(
        make_token(
            "test.signal",
            temporal={
                "uses_future_data": True,
                "window_mode": "trailing",
                "output_available_at": "same_bar_close",
                "max_lookback": None,
            },
        )
    )
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_registry", lambda: registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.validate.get_recipe_registry", empty_recipe_registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.canonicalize.get_registry", lambda: registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.canonicalize.get_recipe_registry", empty_recipe_registry)
    monkeypatch.setattr("quant_strategy_tokenizer.ir.hashing.get_registry", lambda: registry)


def test_research_future_data_validate_passes_with_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_policy_registry(monkeypatch)
    strategy = tmp_path / "future_data.qst.yaml"
    strategy.write_text(FUTURE_DATA_STRATEGY, encoding="utf-8")

    result = runner.invoke(app, ["validate", str(strategy), "--profile", "research"])

    combined = result.output + getattr(result, "stderr", "")
    assert result.exit_code == 0, combined
    assert "valid" in combined
    assert "future_data_warning" in combined


def test_pretrade_future_data_validate_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_policy_registry(monkeypatch)
    strategy = tmp_path / "future_data.qst.yaml"
    strategy.write_text(FUTURE_DATA_STRATEGY, encoding="utf-8")

    result = runner.invoke(app, ["validate", str(strategy), "--profile", "pretrade"])

    assert result.exit_code == 1
    assert "future_data_violation" in result.output


def test_promote_to_pretrade_fails_with_repair_hint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_policy_registry(monkeypatch)
    strategy = tmp_path / "future_data.qst.yaml"
    strategy.write_text(FUTURE_DATA_STRATEGY, encoding="utf-8")

    result = runner.invoke(app, ["promote", str(strategy), "--to", "pretrade"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["validation_failures"][0]["kind"] == "future_data_violation"
    assert payload["validation_failures"][0]["repair_hint"]


def test_p0_p1_backward_compatibility_still_available() -> None:
    result = runner.invoke(app, ["vocabulary", "--check"])

    assert result.exit_code == 0
    assert "P0 frozen baseline:" in result.output
    assert "status: preserved" in result.output
