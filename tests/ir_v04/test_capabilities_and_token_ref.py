from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_strategy_tokenizer.hash_v2 import signature_hash_for_ports_v2
from quant_strategy_tokenizer.ir_v04 import NodeV04, StrategyBodyV04, StrategyIRV04, validate_ir_v04
from quant_strategy_tokenizer.ir_v04.canonical import canonicalize_v04


def test_capabilities_default_to_core() -> None:
    ir = StrategyIRV04(strategy=StrategyBodyV04(id="core_only"))

    assert ir.capabilities == ["core"]
    assert validate_ir_v04(ir).ok


def test_panel_and_custom_runtime_capabilities_fail_in_wp2() -> None:
    ir = StrategyIRV04(
        capabilities=["core", "panel", "custom_token_runtime"],
        strategy=StrategyBodyV04(id="future_caps"),
    )

    result = validate_ir_v04(ir)

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.errors] == [
        "capability_not_accepted",
        "capability_not_accepted",
    ]


def test_capabilities_require_core_and_are_unique() -> None:
    with pytest.raises(ValidationError):
        StrategyIRV04(capabilities=["panel"], strategy=StrategyBodyV04(id="bad"))

    with pytest.raises(ValidationError):
        StrategyIRV04(capabilities=["core", "core"], strategy=StrategyBodyV04(id="bad"))


def test_token_ref_canonicalizes_on_node() -> None:
    ir = StrategyIRV04(
        strategy=StrategyBodyV04(
            id="token_ref",
            nodes=[
                NodeV04(
                    id="n",
                    token="legacy.compat",
                    version=1,
                    token_ref={
                        "namespace": "builtin",
                        "name": "math.add",
                        "version": 1,
                        "behavior_version": 1,
                    },
                )
            ],
        )
    )

    node = canonicalize_v04(ir).strategy.nodes[0]

    assert node.token_ref is not None
    assert node.token_ref.model_dump(mode="json") == {
        "namespace": "builtin",
        "name": "math.add",
        "version": 1,
        "behavior_version": 1,
    }
    assert node.token == "legacy.compat"


def test_signature_hash_includes_token_ref() -> None:
    signature = {"inputs": {}, "outputs": {"value": {"type": "Scalar[float]"}}}
    base = signature_hash_for_ports_v2(signature)
    with_ref = signature_hash_for_ports_v2(
        signature,
        token_ref={
            "namespace": "builtin",
            "name": "math.add",
            "version": 1,
            "behavior_version": 1,
        },
    )

    assert base != with_ref
