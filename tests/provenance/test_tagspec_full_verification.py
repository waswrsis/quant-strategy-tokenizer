from __future__ import annotations

import json

from typer.testing import CliRunner

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.composition.verifier import upgrade_verification
from quant_strategy_tokenizer.provenance.registry import load_tagspec_file

runner = CliRunner()


def test_indicator_ewm_tagspec_full_verification() -> None:
    spec = load_tagspec_file("docs/tagspecs/indicator.ewm.tagspec.yaml")
    upgraded = upgrade_verification(spec)

    assert spec.verification.minimally_attached is True
    assert spec.verification.fully_verified is False
    assert upgraded.verification.minimally_attached is True
    assert upgraded.verification.fully_verified is True
    assert upgraded.verification.contracts_pass is True
    assert upgraded.verification.fuzzing_at_ci_standard is True
    assert upgraded.verification.metamorphic_pass is True


def test_qst_tag_verify_full() -> None:
    result = runner.invoke(
        app,
        ["tag", "verify", "docs/tagspecs/indicator.ewm.tagspec.yaml", "--level", "full"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["level"] == "full"
    assert payload["fully_verified"] is True
    assert payload["verification"]["contracts_pass"] is True


def test_agent_tagspec_verify_full() -> None:
    spec = agent.tagspec_verify("indicator.ewm", level="full")

    assert spec is not None
    assert spec.verification.fully_verified is True
