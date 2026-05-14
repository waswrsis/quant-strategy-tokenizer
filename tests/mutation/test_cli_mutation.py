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
