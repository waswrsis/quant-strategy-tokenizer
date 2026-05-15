"""TokenPack metadata for WP8c Panel operators."""

from __future__ import annotations

from typing import Literal

from quant_strategy_tokenizer.ir_v04 import TokenRefV04
from quant_strategy_tokenizer.numeric_v2 import NumericPolicy, NumericRepresentation
from quant_strategy_tokenizer.panel_v2.operators import (
    PANEL_OPERATOR_TOKENS,
    PANEL_OPS_PACK_ID,
    PANEL_OPS_PACK_VERSION,
    PanelOperatorName,
)
from quant_strategy_tokenizer.ports_v2 import InputSpec, OutputSpec
from quant_strategy_tokenizer.tokens_v2 import TokenPackManifestV2, TokenSpecV2
from quant_strategy_tokenizer.types_v2 import parse_type_spec

PanelOperatorCategory = Literal["panel_operator", "selection_operator"]


def panel_ops_token_pack_v2() -> TokenPackManifestV2:
    """Return the WP8c core TokenPack metadata for Panel operators."""

    return TokenPackManifestV2(
        pack_id=PANEL_OPS_PACK_ID,
        version=PANEL_OPS_PACK_VERSION,
        namespaces=("core",),
        tokens=tuple(_panel_operator_spec(name) for name in PANEL_OPERATOR_TOKENS),
        origin_tier="core",
    )


def _panel_operator_spec(name: PanelOperatorName) -> TokenSpecV2:
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
        inputs=_inputs_for(name),
        outputs=_outputs_for(name),
        params_schema=_params_schema(name),
        purity="pure",
        state={
            "panel_operator": True,
            "category": _category_for(name),
            "wp": "WP8c",
            "reference_semantics": "deterministic",
        },
        numeric_policy=_numeric_policy_for(name),
        risk={"risk_level": "medium"},
        tests=[
            {
                "kind": "reference_helper",
                "deterministic": True,
            }
        ],
    )


def _inputs_for(name: PanelOperatorName) -> dict[str, InputSpec]:
    if name == "panel.mask":
        return {
            "panel": _input("Panel[float]"),
            "mask": _input("Panel[bool]"),
        }
    if name == "panel.residualize":
        return {
            "panel": _input("Panel[float]"),
            "factor": _input("TimeSeries[float]"),
        }
    if name == "selection.to_weights":
        return {"selection": _input("Panel[bool]")}
    return {"panel": _input("Panel[float]")}


def _outputs_for(name: PanelOperatorName) -> dict[str, OutputSpec]:
    if name == "panel.rank":
        return {"ranked": _output("Panel[int]")}
    if name in {"panel.top_k", "panel.bottom_k"}:
        return {"selection": _output("Panel[bool]")}
    if name == "selection.to_weights":
        return {"weights": _output("Panel[decimal]")}
    return {"panel": _output("Panel[float]")}


def _params_schema(name: PanelOperatorName) -> dict[str, object]:
    common_missing = {
        "missing_policy": {
            "enum": ["error_on_missing", "drop_missing", "propagate_missing"],
            "default": "error_on_missing",
        }
    }
    if name == "panel.rank":
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                **common_missing,
                "axis": {"const": "symbol", "default": "symbol"},
                "order": {"enum": ["descending", "ascending"], "default": "descending"},
                "rank_base": {"const": 1, "default": 1},
                "tie_policy": {"const": "stable_symbol_order", "default": "stable_symbol_order"},
            },
        }
    if name == "panel.zscore":
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                **common_missing,
                "axis": {"const": "symbol", "default": "symbol"},
                "ddof": {"const": 0, "default": 0},
                "zero_variance_policy": {"const": "output_zero", "default": "output_zero"},
            },
        }
    if name in {"panel.top_k", "panel.bottom_k"}:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["k"],
            "properties": {
                **common_missing,
                "k": {"type": "integer", "minimum": 1},
                "tie_policy": {"const": "stable_symbol_order", "default": "stable_symbol_order"},
                "selection_size_policy": {"const": "allow_smaller", "default": "allow_smaller"},
            },
        }
    if name == "panel.winsorize":
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                **common_missing,
                "lower_quantile": {"type": "string", "default": "0.01"},
                "upper_quantile": {"type": "string", "default": "0.99"},
                "interpolation": {"const": "nearest_rank", "default": "nearest_rank"},
            },
        }
    if name == "panel.group_demean":
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["group_spec_ref"],
            "properties": {
                **common_missing,
                "group_spec_ref": {"type": "string", "minLength": 1},
                "missing_group_policy": {
                    "enum": ["error", "drop", "assign_unknown"],
                    "default": "error",
                },
            },
        }
    if name == "panel.residualize":
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                **common_missing,
                "include_intercept": {"const": True, "default": True},
                "min_observations": {"type": "integer", "minimum": 3, "default": 3},
                "insufficient_observations_policy": {
                    "enum": ["unknown", "error"],
                    "default": "unknown",
                },
            },
        }
    if name == "selection.to_weights":
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "method": {
                    "enum": ["equal_long", "equal_short", "equal_long_short"],
                    "default": "equal_long",
                },
                "weight_kind": {"const": "raw", "default": "raw"},
                "normalized": {"const": False, "default": False},
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": common_missing,
    }


def _category_for(name: PanelOperatorName) -> PanelOperatorCategory:
    if name == "selection.to_weights":
        return "selection_operator"
    return "panel_operator"


def _numeric_policy_for(name: PanelOperatorName) -> NumericPolicy:
    representation: NumericRepresentation
    if name == "selection.to_weights":
        representation = "decimal"
    elif name in {"panel.top_k", "panel.bottom_k", "panel.mask"}:
        representation = "object"
    else:
        representation = "float64"
    return NumericPolicy(
        representation=representation,
        deterministic_level="semantic",
        reduction_order="fixed_input_order",
        nan_policy="reject",
        inf_policy="reject",
    )


def _input(type_spec: str) -> InputSpec:
    return InputSpec(type=parse_type_spec(type_spec))


def _output(type_spec: str) -> OutputSpec:
    return OutputSpec(type=parse_type_spec(type_spec))
