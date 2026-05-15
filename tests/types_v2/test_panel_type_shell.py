from __future__ import annotations

from quant_strategy_tokenizer.types_v2 import parse_type_spec


def test_panel_type_shell_parses_without_axis_semantics() -> None:
    spec = parse_type_spec("Panel[float]")

    assert spec.kind == "Panel"
    assert spec.value_type is not None
    assert spec.value_type.name == "float"
    assert spec.model_dump(mode="json", exclude_none=True) == {
        "kind": "Panel",
        "value_type": "float",
    }
