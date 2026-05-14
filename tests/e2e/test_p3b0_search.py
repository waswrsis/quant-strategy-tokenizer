from __future__ import annotations

import json

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

runner = CliRunner()


def test_p3b0_search_cli_smoke() -> None:
    token_result = runner.invoke(app, ["search", "token", "--output-type", "TimeSeries[float]"])
    recipe_result = runner.invoke(
        app,
        ["search", "recipe", "--uses-token", "smooth.linear_recursive", "--limit", "20"],
    )
    tagspec_result = runner.invoke(app, ["search", "tagspec", "--fully-verified"])

    assert token_result.exit_code == 0
    assert "data.column" in {item["id"] for item in json.loads(token_result.output)}
    assert recipe_result.exit_code == 0
    assert "indicator.ewm" in {item["id"] for item in json.loads(recipe_result.output)}
    assert tagspec_result.exit_code == 0
    assert [item["id"] for item in json.loads(tagspec_result.output)] == ["indicator.ewm"]
