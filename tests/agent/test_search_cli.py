from __future__ import annotations

import json

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

runner = CliRunner()


def test_search_cli_token_output_type() -> None:
    result = runner.invoke(app, ["search", "token", "--output-type", "TimeSeries[float]"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    ids = {item["id"] for item in payload}
    assert "data.column" in ids
    assert all(item["kind"] == "token" for item in payload)


def test_search_cli_recipe_uses_token_limit() -> None:
    result = runner.invoke(
        app,
        ["search", "recipe", "--uses-token", "smooth.linear_recursive", "--limit", "20"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    ids = {item["id"] for item in payload}
    assert "indicator.ewm" in ids


def test_search_cli_tagspec_fully_verified() -> None:
    result = runner.invoke(app, ["search", "tagspec", "--fully-verified"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [item["id"] for item in payload] == ["indicator.ewm"]


def test_search_cli_empty_result() -> None:
    result = runner.invoke(app, ["search", "recipe", "--domain", "nope"])

    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_search_cli_rejects_unknown_kind() -> None:
    result = runner.invoke(app, ["search", "unknown"])

    assert result.exit_code == 2
    assert "unsupported search kind" in result.output
