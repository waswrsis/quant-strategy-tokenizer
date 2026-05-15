"""Core TokenPack metadata for Token System v2 WP6a state tokens."""

from __future__ import annotations

from quant_strategy_tokenizer.ir_v04 import TokenRefV04
from quant_strategy_tokenizer.numeric_v2 import NumericPolicy
from quant_strategy_tokenizer.ports_v2 import InputSpec, OutputSpec
from quant_strategy_tokenizer.state_v2.policy import default_state_policy
from quant_strategy_tokenizer.tokens_v2 import TokenPackManifestV2, TokenSpecV2
from quant_strategy_tokenizer.types_v2 import parse_type_spec

STATE_BASIC_PACK_ID = "qst-tokenpack-state-basic"
STATE_BASIC_PACK_VERSION = "0.1.0"


def state_basic_token_pack_v2() -> TokenPackManifestV2:
    """Return the accepted WP6a core TokenPack metadata."""

    return TokenPackManifestV2(
        pack_id=STATE_BASIC_PACK_ID,
        version=STATE_BASIC_PACK_VERSION,
        namespaces=("core",),
        tokens=(
            _state_token_spec(
                name="state.delay",
                params_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "steps": {"type": "integer", "minimum": 1, "default": 1},
                        "initial": {},
                    },
                },
                outputs={"y": _output("TimeSeries[object]")},
            ),
            _state_token_spec(
                name="state.accumulate",
                params_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reducer"],
                    "properties": {
                        "reducer": {"enum": ["count", "last", "max", "min", "sum"]},
                        "initial": {},
                    },
                },
                outputs={"y": _output("TimeSeries[object]")},
            ),
            _state_token_spec(
                name="state.edge_detect",
                params_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "mode": {"enum": ["rising", "falling", "change"], "default": "rising"},
                    },
                },
                inputs={"x": _input("TimeSeries[bool]")},
                outputs={"edge": _output("TimeSeries[bool]")},
            ),
        ),
        origin_tier="core",
    )


def _state_token_spec(
    *,
    name: str,
    params_schema: dict[str, object],
    outputs: dict[str, OutputSpec],
    inputs: dict[str, InputSpec] | None = None,
) -> TokenSpecV2:
    return TokenSpecV2(
        token_id=f"core.{name}",
        token_ref=TokenRefV04(
            namespace="core",
            name=name,
            version=1,
            behavior_version=1,
        ),
        version=1,
        behavior_version=1,
        origin_tier="core",
        inputs=inputs or {"x": _input("TimeSeries[object]")},
        outputs=outputs,
        params_schema=params_schema,
        purity="contextual_read",
        state={
            "stateful": True,
            "state_policy": default_state_policy().model_dump(mode="json"),
            "wp": "WP6a",
        },
        numeric_policy=NumericPolicy(
            representation="object",
            deterministic_level="semantic",
            reduction_order="fixed_input_order",
            nan_policy="propagate",
            inf_policy="reject",
        ),
        risk={"risk_level": "medium"},
        tests=[
            {
                "kind": "reference_helper",
                "deterministic": True,
            }
        ],
    )


def _input(type_spec: str) -> InputSpec:
    return InputSpec(type=parse_type_spec(type_spec))


def _output(type_spec: str) -> OutputSpec:
    return OutputSpec(type=parse_type_spec(type_spec))
