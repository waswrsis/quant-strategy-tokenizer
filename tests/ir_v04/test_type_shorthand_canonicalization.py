from __future__ import annotations

from quant_strategy_tokenizer.ir_v04 import NodeV04, StrategyBodyV04, StrategyIRV04
from quant_strategy_tokenizer.ir_v04.canonical import canonical_bytes_v04, canonicalize_v04


def test_node_signature_shorthand_canonicalizes_to_structured_types() -> None:
    ir = StrategyIRV04(
        strategy=StrategyBodyV04(
            id="typed_shell",
            nodes=[
                NodeV04(
                    id="n",
                    signature={
                        "inputs": {"price": {"type": "TimeSeries[float]"}},
                        "outputs": {"signal": {"type": "TimeSeries[bool]"}},
                    },
                )
            ],
        )
    )

    canonical = canonicalize_v04(ir)
    signature = canonical.strategy.nodes[0].signature.model_dump(mode="json", exclude_none=True)

    assert signature == {
        "inputs": {"price": {"type": {"kind": "TimeSeries", "value_type": "float"}}},
        "outputs": {"signal": {"type": {"kind": "TimeSeries", "value_type": "bool"}}},
    }


def test_node_signature_does_not_replace_graph_inputs() -> None:
    node = NodeV04(
        id="n",
        inputs={"series": "source.close"},
        signature={"inputs": {"series": {"type": "TimeSeries[float]"}}},
    )

    assert node.inputs == {"series": "source.close"}
    assert "series" in node.signature.inputs


def test_canonical_bytes_support_signature_without_intrinsic_temporal() -> None:
    ir = StrategyIRV04(
        strategy=StrategyBodyV04(
            id="bytes",
            nodes=[
                NodeV04(
                    id="n",
                    signature={
                        "inputs": {
                            "price": {
                                "type": "TimeSeries[float]",
                                "temporal_requirement": {
                                    "max_available_at": "bar_close",
                                    "allow_unsafe_future": False,
                                },
                            }
                        },
                        "outputs": {"signal": {"type": "Decision"}},
                    },
                )
            ],
        )
    )

    assert canonical_bytes_v04(ir) == canonical_bytes_v04(ir.model_dump(mode="json"))
