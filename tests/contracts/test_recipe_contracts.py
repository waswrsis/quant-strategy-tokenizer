from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.composition.contract import (
    contracts_pass,
    load_contract_suite,
    run_contract_suite,
)

CONTRACTS = Path("docs/contracts/indicator.ewm.contracts.yaml")


def test_indicator_ewm_contracts_pass() -> None:
    suite = load_contract_suite(CONTRACTS)

    assert suite.recipe == "indicator.ewm"
    assert suite.version == 1
    assert contracts_pass(CONTRACTS)
    assert all(result.passed for result in run_contract_suite(CONTRACTS))


def test_bad_recipe_contract_fails(tmp_path: Path) -> None:
    bad = tmp_path / "bad.contracts.yaml"
    bad.write_text(
        """
recipe: indicator.ewm
version: 1
cases:
  - name: intentionally_wrong
    params: {span: 3, init: first_value}
    inputs:
      series: [1.0, 2.0, 3.0]
    expected_outputs:
      value: [0.0, 0.0, 0.0]
""",
        encoding="utf-8",
    )

    results = run_contract_suite(bad)
    assert len(results) == 1
    assert results[0].passed is False
    assert contracts_pass(bad) is False
