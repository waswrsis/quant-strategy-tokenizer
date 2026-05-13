from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.parse.yaml_loader import (
    load_strategy_file,
    load_strategy_file_with_envelope,
    load_strategy_with_envelope,
)

ROOT = Path(__file__).resolve().parents[2]


def test_load_strategy_without_envelope_defaults_to_research() -> None:
    path = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
    ir = load_strategy_file(path)
    loaded_ir, envelope = load_strategy_file_with_envelope(path)

    assert loaded_ir == ir
    assert envelope.profile == "research"
    assert envelope.strategy_instance_hash == compute_hashes(ir).instance_hash


def test_load_strategy_with_envelope_does_not_enter_ir() -> None:
    yaml_text = """
_envelope:
  profile: paper
  approved_by: reviewer
  notes: smoke
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: s
strategy_version: 1
form: surface
externals: {}
recipes: []
graph: []
outputs: {}
"""

    ir, envelope = load_strategy_with_envelope(yaml_text)

    assert ir.strategy == "s"
    assert not hasattr(ir, "_envelope")
    assert envelope.profile == "paper"
    assert envelope.approved_by == "reviewer"
    assert envelope.notes == "smoke"
    assert envelope.strategy_instance_hash == compute_hashes(ir).instance_hash


def test_deployment_envelope_roundtrip() -> None:
    envelope = DeploymentEnvelope(
        strategy_instance_hash="sha256:" + "0" * 64,
        profile="pretrade",
        notes="ready",
    )

    parsed = DeploymentEnvelope.model_validate_json(envelope.model_dump_json())

    assert parsed == envelope
