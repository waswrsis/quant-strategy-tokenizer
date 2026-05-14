from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy, load_strategy_file
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML, P1_PRETRADE_READY_YAML

runner = CliRunner()


def test_qst_diff_outputs_json_report(tmp_path: Path) -> None:
    left = tmp_path / "left.qst.yaml"
    right = tmp_path / "right.qst.yaml"
    left.write_text(P1_PRETRADE_READY_YAML, encoding="utf-8")
    right.write_text(
        P1_PRETRADE_READY_YAML.replace("max_position: 5", "max_position: 10"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["diff", str(left), str(right)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["graph_equal"] is True
    assert payload["param_equal"] is False
    assert payload["param_diffs"][0]["path"] == "graph.risk.params.max_position"


def test_qst_mutate_applies_repair_hint_and_writes_yaml(tmp_path: Path) -> None:
    strategy = tmp_path / "missing.qst.yaml"
    repair = tmp_path / "repair.json"
    output = tmp_path / "repaired.qst.yaml"
    strategy.write_text(P1_MISSING_RISK_PATH_YAML, encoding="utf-8")
    failure = validate(load_strategy(P1_MISSING_RISK_PATH_YAML), profile="pretrade").failures[0]
    assert failure.repair_hint is not None
    repair.write_text(json.dumps(failure.repair_hint), encoding="utf-8-sig")

    result = runner.invoke(
        app,
        ["mutate", str(strategy), "--repair-hint", str(repair), "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["before_hashes"]["instance_hash"] != payload["after_hashes"]["instance_hash"]
    assert output.exists()
    repaired = load_strategy_file(output)
    assert validate(repaired, profile="pretrade").ok


def test_qst_mutate_replace_token_json(tmp_path: Path) -> None:
    strategy = tmp_path / "replace.qst.yaml"
    strategy.write_text(
        """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: replace_cli
strategy_version: 1
form: surface
externals:
  market:
    type: Frame
    required: true
recipes: []
graph:
  - id: close
    token: data.column
    v: 1
    params: {column: close}
    inputs: {frame: market}
  - id: open
    token: data.column
    v: 1
    params: {column: open}
    inputs: {frame: market}
  - id: signal
    token: compare.gt
    v: 1
    params: {}
    inputs: {a: close.value, b: open.value}
outputs:
  signal: signal.value
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mutate",
            str(strategy),
            "--op",
            '{"kind":"replace_token","node_id":"signal","new_token":"compare.ge"}',
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["ir"]["graph"][2]["token"] == "compare.ge"


def test_qst_mutate_inline_recipe_writes_yaml(tmp_path: Path) -> None:
    strategy = tmp_path / "inline.qst.yaml"
    output = tmp_path / "inlined.qst.yaml"
    strategy.write_text(
        """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: inline_cli
strategy_version: 1
form: surface
externals:
  market:
    type: Frame[OHLCV]
    required: true
recipes:
  - id: ema
    recipe: indicator.ewm
    version: 1
    params: {span: 3}
    inputs: {series: market.close}
graph: []
outputs:
  value: ema.value
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mutate",
            str(strategy),
            "--op",
            '{"kind":"inline_recipe","recipe_id":"ema"}',
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    inlined = load_strategy_file(output)
    assert inlined.recipes == []
    assert inlined.graph[0].id == "ema.ewm"
    assert inlined.outputs["value"] == "ema.ewm.value"
