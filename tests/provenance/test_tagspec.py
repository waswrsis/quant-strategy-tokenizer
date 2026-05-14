from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.provenance.registry import (
    get_tagspec_registry,
    load_tagspec_file,
)

ROOT = Path(__file__).resolve().parents[2]
TAGSPEC = ROOT / "docs" / "tagspecs" / "indicator.ewm.tagspec.yaml"


def test_indicator_ewm_tagspec_loads_and_verifies() -> None:
    spec = load_tagspec_file(TAGSPEC)

    assert spec.semantic_id == "indicator.ewm"
    assert spec.version == 1
    assert spec.source_recipe == "indicator.ewm"
    assert spec.verification.minimally_attached is True
    assert spec.verification.fully_verified is False


def test_builtin_tagspec_registry_resolves_indicator_ewm() -> None:
    spec = get_tagspec_registry().get("indicator.ewm", 1)

    assert spec.semantic_id == "indicator.ewm"
    assert spec.verification.minimally_attached is True
