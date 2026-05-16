"""Built-in public TokenPack vocabulary."""

from __future__ import annotations

from typing import Any, Literal

from qst.decision import decision_algebra_token_pack_v2
from qst.ir import TokenRefV04
from qst.numeric import NumericPolicy
from qst.panel import panel_ops_token_pack_v2, panel_weights_token_pack_v2
from qst.ports import InputSpec, OutputSpec
from qst.state import state_basic_token_pack_v2, state_fsm_token_pack_v2
from qst.tokens.pack import TokenPackManifestV2
from qst.tokens.spec import TokenRiskSpec, TokenSpecV2
from qst.tokens.surface import (
    ExecutionSupport,
    TokenFamily,
    TokenLayer,
    TokenMaturity,
    token_surface,
)
from qst.types import parse_type_spec

CORE_SURFACE_PACK_ID = "qst-tokenpack-core-surface"
CORE_SURFACE_PACK_VERSION = "0.1.0"


def builtin_token_packs() -> tuple[TokenPackManifestV2, ...]:
    """Return built-in TokenPacks in deterministic public vocabulary order."""

    packs = (
        core_surface_token_pack_v2(),
        decision_algebra_token_pack_v2(),
        state_basic_token_pack_v2(),
        state_fsm_token_pack_v2(),
        panel_ops_token_pack_v2(),
        panel_weights_token_pack_v2(),
    )
    return tuple(sorted(packs, key=lambda pack: pack.pack_id))


def core_surface_token_pack_v2() -> TokenPackManifestV2:
    """Return Stage 3A core surface TokenSpecs."""

    return TokenPackManifestV2(
        pack_id=CORE_SURFACE_PACK_ID,
        version=CORE_SURFACE_PACK_VERSION,
        namespaces=("core",),
        tokens=tuple(_spec(**item) for item in _TOKEN_DEFINITIONS),
        origin_tier="core",
    )


_Numeric = Literal["float64", "bool", "decimal", "object"]


def _spec(
    *,
    name: str,
    family: TokenFamily,
    category: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
    params_schema: dict[str, object] | None = None,
    numeric: _Numeric = "float64",
    layer: TokenLayer = "derived",
    maturity: TokenMaturity = "accepted",
    execution_support: ExecutionSupport = "reference_helper",
    stateful: bool = False,
    panel_aware: bool = False,
    solver_backed: bool = False,
    external_code: bool = False,
    reserved_only: bool = False,
    risk_level: str = "low",
    temporal: str = "declared_by_ports",
    missing_data: str = "reject_or_declared_by_token",
    failure_mode: str = "diagnostic_error",
    usage_notes: tuple[str, ...] = (),
) -> TokenSpecV2:
    return TokenSpecV2(
        token_id=f"core.{name}",
        token_ref=TokenRefV04(namespace="core", name=name, version=1, behavior_version=1),
        version=1,
        behavior_version=1,
        origin_tier="core",
        inputs={key: InputSpec(type=parse_type_spec(value)) for key, value in inputs.items()},
        outputs={key: OutputSpec(type=parse_type_spec(value)) for key, value in outputs.items()},
        params_schema=params_schema or {"type": "object", "additionalProperties": True},
        purity="pure",
        state={"token_surface_stage": "3A", "category": category},
        numeric_policy=_numeric_policy(numeric),
        risk=TokenRiskSpec(risk_level=risk_level),  # type: ignore[arg-type]
        surface=token_surface(
            family=family,
            category=category,
            layer=layer,
            maturity=maturity,
            execution_support=execution_support,
            contract_scope=(
                "validation_only" if execution_support == "metadata_only" else "reference_semantics"
            ),
            temporal=temporal,
            numeric=(
                "semantic_float64"
                if numeric == "float64"
                else "declared_by_numeric_policy"
            ),
            missing_data=missing_data,
            failure_mode=failure_mode,
            state="stateful reference semantics" if stateful else None,
            panel="panel-aware token" if panel_aware else None,
            stateful=stateful,
            panel_aware=panel_aware,
            solver_backed=solver_backed,
            external_code=external_code,
            reserved_only=reserved_only,
            deterministic_level=(
                "reserved"
                if reserved_only
                else "semantic_float64"
                if numeric == "float64"
                else "reference_exact"
            ),
            examples=(f"core.{name}/v1/bv1",),
            usage_notes=usage_notes,
        ),
        tests=[{"kind": execution_support, "deterministic": execution_support != "metadata_only"}],
    )


def _numeric_policy(kind: _Numeric) -> NumericPolicy:
    representation = {
        "float64": "float64",
        "bool": "bool",
        "decimal": "decimal",
        "object": "object",
    }[kind]
    return NumericPolicy(
        representation=representation,  # type: ignore[arg-type]
        deterministic_level="semantic",
        reduction_order="fixed_input_order",
        nan_policy="reject",
        inf_policy="reject",
    )


_TS_FLOAT = "TimeSeries[float]"
_TS_BOOL = "TimeSeries[bool]"
_TS_OBJECT = "TimeSeries[object]"
_EVENT_FLOAT = "EventStream[float]"
_EVENT_BOOL = "EventStream[bool]"
_DECISION = "Decision"
_PLAN = "Plan"
_PANEL_FLOAT = "Panel[float]"
_PANEL_DECIMAL = "Panel[decimal]"

_EMPTY_INPUT_POLICY = (
    "Empty fold inputs are validation errors unless explicitly allowed by params.",
)

_MATH_PARAMS: dict[str, object] = {"type": "object", "additionalProperties": False}
_BINARY_PARAMS: dict[str, object] = {"type": "object", "additionalProperties": False}
_UNARY_PARAMS: dict[str, object] = {"type": "object", "additionalProperties": False}
_CLIP_PARAMS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["lower", "upper"],
    "properties": {"lower": {"type": "number"}, "upper": {"type": "number"}},
}
_ROUND_PARAMS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"ndigits": {"type": "integer", "default": 0}},
}
_FILL_NAN_PARAMS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["replacement"],
    "properties": {"replacement": {"type": "number"}},
}
_ALLOW_EMPTY_PARAMS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"allow_empty": {"type": "boolean", "default": False}},
}
_BETWEEN_PARAMS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"inclusive": {"type": "boolean", "default": True}},
}

_TOKEN_DEFINITIONS: tuple[dict[str, Any], ...] = (
    # Math and boolean primitives.
    {"name": "math.add", "family": "math", "category": "arithmetic", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "math.sub", "family": "math", "category": "arithmetic", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "math.mul", "family": "math", "category": "arithmetic", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "math.div", "family": "math", "category": "arithmetic", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "failure_mode": "division_by_zero emits diagnostic error"},
    {"name": "math.neg", "family": "math", "category": "arithmetic", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.abs", "family": "math", "category": "arithmetic", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.pow", "family": "math", "category": "arithmetic", "inputs": {"base": _TS_FLOAT, "exponent": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _BINARY_PARAMS},
    {"name": "math.sqrt", "family": "math", "category": "arithmetic", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS, "failure_mode": "negative input emits diagnostic error"},
    {"name": "math.log", "family": "math", "category": "arithmetic", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS, "failure_mode": "non-positive input emits diagnostic error"},
    {"name": "math.exp", "family": "math", "category": "arithmetic", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.min", "family": "math", "category": "reduction", "inputs": {"values": _EVENT_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _ALLOW_EMPTY_PARAMS, "failure_mode": "empty input emits diagnostic error unless allow_empty=true", "usage_notes": _EMPTY_INPUT_POLICY},
    {"name": "math.max", "family": "math", "category": "reduction", "inputs": {"values": _EVENT_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _ALLOW_EMPTY_PARAMS, "failure_mode": "empty input emits diagnostic error unless allow_empty=true", "usage_notes": _EMPTY_INPUT_POLICY},
    {"name": "math.clip", "family": "math", "category": "transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _CLIP_PARAMS, "failure_mode": "lower greater than upper emits diagnostic error"},
    {"name": "math.floor", "family": "math", "category": "transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.ceil", "family": "math", "category": "transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.round", "family": "math", "category": "transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _ROUND_PARAMS},
    {"name": "math.sign", "family": "math", "category": "transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _UNARY_PARAMS},
    {"name": "math.isnan", "family": "math", "category": "predicate", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "params_schema": _UNARY_PARAMS, "numeric": "bool", "missing_data": "declared NaN predicate handling"},
    {"name": "math.isfinite", "family": "math", "category": "predicate", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "params_schema": _UNARY_PARAMS, "numeric": "bool", "missing_data": "declared finite predicate handling"},
    {"name": "math.where", "family": "math", "category": "conditional", "inputs": {"condition": _TS_BOOL, "if_true": _TS_FLOAT, "if_false": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _MATH_PARAMS},
    {"name": "math.fill_nan", "family": "math", "category": "missing_transform", "inputs": {"x": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "params_schema": _FILL_NAN_PARAMS, "missing_data": "NaN values are replaced by explicit replacement parameter"},
    {"name": "bool.and", "family": "bool", "category": "boolean_logic", "inputs": {"a": _TS_BOOL, "b": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "bool.or", "family": "bool", "category": "boolean_logic", "inputs": {"a": _TS_BOOL, "b": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "bool.not", "family": "bool", "category": "boolean_logic", "inputs": {"x": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "bool.xor", "family": "bool", "category": "boolean_logic", "inputs": {"a": _TS_BOOL, "b": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "bool.any", "family": "bool", "category": "boolean_reduction", "inputs": {"values": _EVENT_BOOL}, "outputs": {"value": _TS_BOOL}, "params_schema": _ALLOW_EMPTY_PARAMS, "numeric": "bool", "failure_mode": "empty input emits diagnostic error unless allow_empty=true", "usage_notes": _EMPTY_INPUT_POLICY},
    {"name": "bool.all", "family": "bool", "category": "boolean_reduction", "inputs": {"values": _EVENT_BOOL}, "outputs": {"value": _TS_BOOL}, "params_schema": _ALLOW_EMPTY_PARAMS, "numeric": "bool", "failure_mode": "empty input emits diagnostic error unless allow_empty=true", "usage_notes": _EMPTY_INPUT_POLICY},
    {"name": "bool.count_true", "family": "bool", "category": "boolean_reduction", "inputs": {"values": _EVENT_BOOL}, "outputs": {"value": "TimeSeries[int]"}, "params_schema": _ALLOW_EMPTY_PARAMS, "numeric": "object", "failure_mode": "empty input emits diagnostic error unless allow_empty=true", "usage_notes": _EMPTY_INPUT_POLICY},
    {"name": "logic.and", "family": "bool", "category": "boolean_logic", "inputs": {"a": _TS_BOOL, "b": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "logic.or", "family": "bool", "category": "boolean_logic", "inputs": {"a": _TS_BOOL, "b": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "logic.not", "family": "bool", "category": "boolean_logic", "inputs": {"x": _TS_BOOL}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.eq", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.ne", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.gt", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.gte", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.lt", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.lte", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "cmp.between", "family": "compare", "category": "range_comparison", "inputs": {"x": _TS_FLOAT, "lower": _TS_FLOAT, "upper": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "params_schema": _BETWEEN_PARAMS, "numeric": "bool", "failure_mode": "lower greater than upper emits diagnostic error"},
    {"name": "cmp.outside", "family": "compare", "category": "range_comparison", "inputs": {"x": _TS_FLOAT, "lower": _TS_FLOAT, "upper": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "params_schema": _BETWEEN_PARAMS, "numeric": "bool", "failure_mode": "lower greater than upper emits diagnostic error"},
    {"name": "compare.gt", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "compare.ge", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "compare.lt", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "compare.le", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "compare.eq", "family": "compare", "category": "comparison", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    # Data, time, alignment, window, signal, and indicators.
    {"name": "data.shift", "family": "data", "category": "lag", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "temporal": "positive periods lag; negative periods require unsafe-future diagnostics"},
    {"name": "data.identity", "family": "data", "category": "identity", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "time.session_filter", "family": "time", "category": "calendar_filter", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "align.inner_join", "family": "align", "category": "alignment", "inputs": {"left": _TS_FLOAT, "right": _TS_FLOAT}, "outputs": {"left": _TS_FLOAT, "right": _TS_FLOAT}},
    {"name": "align.forward_fill", "family": "align", "category": "alignment", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "window.max", "family": "window", "category": "rolling_window", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "temporal": "min_history_bars derives from window parameter"},
    {"name": "window.min", "family": "window", "category": "rolling_window", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "temporal": "min_history_bars derives from window parameter"},
    {"name": "window.mean", "family": "window", "category": "rolling_window", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "temporal": "min_history_bars derives from window parameter"},
    {"name": "window.std", "family": "window", "category": "rolling_window", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "temporal": "min_history_bars derives from window parameter"},
    {"name": "norm.range_position", "family": "signal", "category": "normalization", "inputs": {"value": _TS_FLOAT, "high": _TS_FLOAT, "low": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "smooth.linear_recursive", "family": "signal", "category": "smoothing", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "stateful": True},
    {"name": "signal.cross_above", "family": "signal", "category": "cross", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "signal.cross_below", "family": "signal", "category": "cross", "inputs": {"a": _TS_FLOAT, "b": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    {"name": "indicator.ema", "family": "indicator", "category": "trend", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}, "stateful": True},
    {"name": "indicator.rsi", "family": "indicator", "category": "oscillator", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_FLOAT}},
    {"name": "indicator.bollinger", "family": "indicator", "category": "band", "inputs": {"series": _TS_FLOAT}, "outputs": {"middle": _TS_FLOAT, "upper": _TS_FLOAT, "lower": _TS_FLOAT}},
    {"name": "indicator.channel_breakout", "family": "indicator", "category": "breakout", "inputs": {"high": _TS_FLOAT, "low": _TS_FLOAT, "close": _TS_FLOAT}, "outputs": {"value": _TS_BOOL}, "numeric": "bool"},
    # Decision, gate, risk, and plan surface tokens.
    {"name": "decision.lift_bool", "family": "decision", "category": "decision_bridge", "inputs": {"series": _TS_BOOL}, "outputs": {"decision": _DECISION}, "numeric": "object"},
    {"name": "gate.cooldown", "family": "gate", "category": "state_gate", "inputs": {"decision": _DECISION}, "outputs": {"decision": _DECISION}, "numeric": "object", "stateful": True},
    {"name": "gate.circuit_breaker", "family": "gate", "category": "state_gate", "inputs": {"decision": _DECISION}, "outputs": {"decision": _DECISION}, "numeric": "object", "stateful": True},
    {"name": "risk.position_cap", "family": "risk", "category": "risk_gate", "inputs": {"decision": _DECISION, "state": "State[object]"}, "outputs": {"decision": _DECISION}, "numeric": "object", "risk_level": "medium"},
    {"name": "risk.volatility_target", "family": "risk", "category": "weight_risk", "inputs": {"weights": _PANEL_DECIMAL, "volatility": _PANEL_FLOAT}, "outputs": {"weights": _PANEL_DECIMAL}, "numeric": "decimal", "panel_aware": True, "risk_level": "medium"},
    {"name": "risk.turnover_cap", "family": "risk", "category": "weight_risk", "inputs": {"weights": _PANEL_DECIMAL, "previous": _PANEL_DECIMAL}, "outputs": {"weights": _PANEL_DECIMAL}, "numeric": "decimal", "panel_aware": True, "risk_level": "medium"},
    {"name": "plan.noop", "family": "execution", "category": "plan_shell", "inputs": {"decision": _DECISION}, "outputs": {"plan": _PLAN}, "numeric": "object", "execution_support": "metadata_only"},
    {"name": "plan.order_intent", "family": "execution", "category": "plan_shell", "inputs": {"decision": _DECISION, "sizing": "Scalar[float]"}, "outputs": {"plan": _PLAN}, "numeric": "object", "execution_support": "metadata_only"},
    # Experimental optimizer and reserved design boundaries.
    {"name": "optimizer.mean_variance", "family": "optimizer", "category": "portfolio_optimizer", "inputs": {"expected_return": _PANEL_FLOAT, "risk": _PANEL_FLOAT}, "outputs": {"weights": _PANEL_DECIMAL}, "numeric": "decimal", "maturity": "experimental", "panel_aware": True, "solver_backed": True, "risk_level": "high", "usage_notes": ("Requires explicit solver determinism contract before promotion.",)},
    {"name": "event.join_asof", "family": "event", "category": "event_stream", "inputs": {"events": "EventStream[object]"}, "outputs": {"events": "EventStream[object]"}, "numeric": "object", "maturity": "reserved_design", "execution_support": "metadata_only", "reserved_only": True},
    {"name": "distribution.normal_fit", "family": "distribution", "category": "distribution_model", "inputs": {"series": _TS_FLOAT}, "outputs": {"value": _TS_OBJECT}, "numeric": "object", "maturity": "reserved_design", "execution_support": "metadata_only", "reserved_only": True},
    {"name": "score.zscore", "family": "continuous_score", "category": "score_transform", "inputs": {"series": _TS_FLOAT}, "outputs": {"score": _TS_FLOAT}},
)
