from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.mutation import ReplaceToken, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy

COMPARE_STRATEGY = """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: replace_token_demo
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
    inputs:
      a: close.value
      b: open.value
outputs:
  signal: signal.value
"""


def test_replace_token_accepts_type_compatible_token() -> None:
    ir = load_strategy(COMPARE_STRATEGY)

    result = mutate_strategy(
        ir,
        ReplaceToken(node_id="signal", new_token="compare.ge"),
    )

    assert result.ok, result.error
    assert result.ir is not None
    assert result.ir.graph[2].token == "compare.ge"
    assert result.ir.outputs["signal"] == "signal.value"
    assert validate(result.ir).ok
    assert result.before_hashes["graph_hash"] != result.after_hashes["graph_hash"]


def test_replace_token_rejects_output_type_incompatibility() -> None:
    ir = load_strategy(COMPARE_STRATEGY)

    result = mutate_strategy(
        ir,
        ReplaceToken(
            node_id="signal",
            new_token="decision.lift_bool",
            new_params={"reason": "entry"},
            input_mapping={"value": "a"},
        ),
    )

    assert not result.ok
    assert "missing used output port" in (result.error or "")


def test_replace_token_rejects_input_type_incompatibility() -> None:
    ir = load_strategy(COMPARE_STRATEGY)

    result = mutate_strategy(
        ir,
        ReplaceToken(node_id="signal", new_token="data.shift", input_mapping={"series": "a"}),
    )

    assert not result.ok
    assert "output 'value' type mismatch" in (result.error or "")
