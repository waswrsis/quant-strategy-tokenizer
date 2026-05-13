"""
quant_strategy_tokenizer.indicators.derivatives_common
======================================================
Purpose: shared implementation layer for atomic derivatives indicator tokens.
Core idea: Normalize caller-supplied futures/perpetual time series, option-chain
long rows, or already aggregated derivatives diagnostics, then compute funding,
open-interest, basis, liquidation, positioning, implied-volatility, skew,
put-call, and Greeks-exposure diagnostics. Assumes derivatives data describes
leverage, crowding, and volatility regime but does not make trading decisions by
itself.
Inputs: raw user data, optional DataFrameSpec/ExtractorSpec, DerivativesParams,
indicator name, and ModuleRunContext.
Outputs: DerivativesReport wrapped in ModuleResult with latest values,
direction, risk/crowding/term-structure states, pressure fields, optional
series, diagnostics, warnings, and report files when requested.
Failure semantics: invalid params, missing fields, unsupported input shapes,
insufficient history, zero denominators, unusable option chains, missing OI or
volume, and calculation errors return ModuleResult.fail.
Market generalization: calculations operate on caller-mapped numeric fields and
do not assume asset class, venue, symbol format, exchange API, broker, or live
account access.
"""
from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..reporting import write_module_report


@dataclass
class DerivativesParams:
    """Generic derivatives-indicator options used by atomic wrapper modules.

    Configuration:
    - field names map caller data into futures/perp prices, funding, OI, basis,
      positioning, liquidation, and option-chain fields.
    - window fields are rows/bars on the input time axis.
    - thresholds label risk, crowding, liquidation, and extreme z-score states.
    - option term settings define near/far expiry buckets in calendar days.
    """

    ts_field: str = "ts"
    price_field: str = "price"
    mark_price_field: str = "mark_price"
    index_price_field: str = "index_price"
    spot_price_field: str = "spot_price"
    funding_rate_field: str = "funding_rate"
    open_interest_field: str = "open_interest"
    basis_field: str = "basis"
    premium_field: str = "premium"
    long_short_ratio_field: str = "long_short_ratio"
    taker_buy_sell_ratio_field: str = "taker_buy_sell_ratio"
    liquidation_long_field: str = "liquidation_long"
    liquidation_short_field: str = "liquidation_short"
    option_type_field: str = "option_type"
    strike_field: str = "strike"
    expiry_field: str = "expiry"
    underlying_price_field: str = "underlying_price"
    mark_iv_field: str = "mark_iv"
    delta_field: str = "delta"
    gamma_field: str = "gamma"
    vega_field: str = "vega"
    theta_field: str = "theta"
    volume_field: str = "volume"
    realized_volatility_field: str = "realized_volatility"
    window: int = 20
    fast_window: int = 5
    slow_window: int = 30
    regime_window: int = 100
    term_structure_near_days: int = 30
    term_structure_far_days: int = 90
    high_percentile: float = 80.0
    low_percentile: float = 20.0
    extreme_zscore: float = 2.0
    crowding_threshold: float = 70.0
    liquidation_threshold: float = 70.0
    periods_per_year: int = 365


@dataclass
class DerivativesReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    derivative_direction: str = "unknown"
    risk_state: str = "unknown"
    crowding_state: str = "unknown"
    term_structure_state: str = "unknown"
    leverage_pressure: Optional[float] = None
    funding_pressure: Optional[float] = None
    oi_pressure: Optional[float] = None
    liquidation_pressure: Optional[float] = None
    skew_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    series: Optional[List[Optional[float]]] = None
    series_by_name: Optional[Dict[str, List[Optional[float]]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _DerivativesData:
    kind: str
    frame: pd.DataFrame
    used_fields: Dict[str, str] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class _ComputeOutput:
    primary: pd.Series
    series: Dict[str, pd.Series]
    derivative_direction: str = "unknown"
    risk_state: str = "unknown"
    crowding_state: str = "unknown"
    term_structure_state: str = "unknown"
    leverage_pressure: Optional[float] = None
    funding_pressure: Optional[float] = None
    oi_pressure: Optional[float] = None
    liquidation_pressure: Optional[float] = None
    skew_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


FUTURES_INDICATORS = {
    "funding_rate",
    "funding_rate_zscore",
    "funding_momentum",
    "funding_regime",
    "funding_crowding_score",
    "open_interest_change",
    "open_interest_roc",
    "open_interest_zscore",
    "price_oi_divergence",
    "oi_volume_ratio",
    "basis_rate",
    "basis_zscore",
    "basis_momentum",
    "premium_index",
    "mark_index_deviation",
    "perp_spot_deviation",
    "long_short_ratio",
    "long_short_ratio_zscore",
    "taker_buy_sell_ratio",
    "taker_flow_imbalance",
    "leverage_pressure_index",
    "liquidation_imbalance",
    "liquidation_pressure",
    "long_liquidation_ratio",
    "short_liquidation_ratio",
    "liquidation_cascade_risk",
    "derivatives_crowding_index",
    "perp_risk_regime",
    "futures_curve_pressure",
}

OPTIONS_INDICATORS = {
    "implied_volatility",
    "iv_rank",
    "iv_percentile",
    "iv_term_structure",
    "front_back_iv_spread",
    "put_call_iv_skew",
    "risk_reversal",
    "butterfly_skew",
    "smile_curvature",
    "atm_iv_skew",
    "put_call_volume_ratio",
    "put_call_open_interest_ratio",
    "option_volume_oi_ratio",
    "gamma_exposure",
    "delta_exposure",
    "vega_exposure",
    "theta_exposure",
    "dealer_gamma_proxy",
    "options_crowding_index",
    "volatility_risk_premium_proxy",
    "max_pain_proxy",
}


def normalize_derivatives_input(request: Any) -> ModuleResult[_DerivativesData]:
    params = request.params
    spec = request.spec or DataFrameSpec()
    raw = _raw_to_frame(request.data, request.extractor)
    if not raw.ok:
        return raw
    frame = raw.value
    if frame is None or frame.empty:
        return ModuleResult.fail("empty_input", "derivatives input contains no rows")
    frame = frame.copy()
    cols = {str(c): c for c in frame.columns}
    used: Dict[str, str] = {}
    field_candidates = {
        "ts": [params.ts_field, spec.ts_col],
        "price": [params.price_field, spec.price_col, spec.value_col, spec.close_col],
        "mark_price": [params.mark_price_field],
        "index_price": [params.index_price_field],
        "spot_price": [params.spot_price_field],
        "funding_rate": [params.funding_rate_field],
        "open_interest": [params.open_interest_field],
        "basis": [params.basis_field],
        "premium": [params.premium_field],
        "long_short_ratio": [params.long_short_ratio_field],
        "taker_buy_sell_ratio": [params.taker_buy_sell_ratio_field],
        "liquidation_long": [params.liquidation_long_field],
        "liquidation_short": [params.liquidation_short_field],
        "option_type": [params.option_type_field],
        "strike": [params.strike_field],
        "expiry": [params.expiry_field],
        "underlying_price": [params.underlying_price_field],
        "mark_iv": [params.mark_iv_field],
        "delta": [params.delta_field],
        "gamma": [params.gamma_field],
        "vega": [params.vega_field],
        "theta": [params.theta_field],
        "volume": [params.volume_field, spec.volume_col],
        "realized_volatility": [params.realized_volatility_field],
    }
    for logical, names in field_candidates.items():
        col = _find_any_col(cols, names)
        if col is not None:
            used[logical] = str(col)

    if "ts" in used:
        converted = pd.to_datetime(frame[used["ts"]], utc=True, errors="coerce")
        if converted.isna().any():
            return ModuleResult.fail("invalid_timestamp", "timestamp field contains invalid values", field=used["ts"])
        frame["__ts"] = converted
    else:
        frame["__ts"] = pd.RangeIndex(len(frame))

    for logical, col in used.items():
        if logical in {"ts", "option_type", "expiry"}:
            continue
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if "expiry" in used:
        expiry = pd.to_datetime(frame[used["expiry"]], utc=True, errors="coerce")
        if expiry.isna().any():
            return ModuleResult.fail("invalid_timestamp", "expiry field contains invalid values", field=used["expiry"])
        frame["__expiry"] = expiry
    if "option_type" in used:
        frame["__option_type"] = frame[used["option_type"]].astype(str).str.lower().str.strip().map(_normalize_option_type)

    kind = "options" if {"option_type", "strike", "expiry"}.issubset(used) else "futures"
    frame = frame.sort_values("__ts").reset_index(drop=True)
    profile = {"input_type": type(request.data).__name__, "rows": int(len(frame)), "columns": [str(c) for c in frame.columns if not str(c).startswith("__")]}
    return ModuleResult.success(_DerivativesData(kind=kind, frame=frame, used_fields=used, input_profile=profile, warnings=list(raw.warnings)))


def run_derivatives_indicator(indicator: str, request: Any, *, module_name: str) -> ModuleResult[DerivativesReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error
    norm = normalize_derivatives_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    data = norm.value
    if data is None:
        return ModuleResult.fail("internal_error", "derivatives normalization returned no data")

    missing = _missing_required_fields(indicator, data)
    if missing:
        return ModuleResult.fail("missing_required_field", f"{indicator} requires fields: {missing}", details={"missing_fields": missing})
    min_rows = _minimum_rows(indicator, params)
    row_count = _time_row_count(data)
    if row_count < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} time rows, got {row_count}")

    try:
        computed = _compute_options(indicator, params, data) if indicator in OPTIONS_INDICATORS else _compute_futures(indicator, params, data)
    except Exception as exc:
        return ModuleResult.fail("calculation_error", f"{indicator} calculation failed", details={"error": str(exc), "error_type": type(exc).__name__})

    primary = computed.primary.replace([np.inf, -np.inf], np.nan)
    last = _last_float(primary)
    if last is None:
        return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output")
    series_map = {name: ser.replace([np.inf, -np.inf], np.nan) for name, ser in computed.series.items()}
    if "value" not in series_map:
        series_map["value"] = primary
    last_values = {name: _last_float(ser) for name, ser in series_map.items()}
    include_series = detail_at_least(request.context.detail_level, DetailLevel.FULL)
    report = DerivativesReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        derivative_direction=computed.derivative_direction,
        risk_state=computed.risk_state,
        crowding_state=computed.crowding_state,
        term_structure_state=computed.term_structure_state,
        leverage_pressure=computed.leverage_pressure,
        funding_pressure=computed.funding_pressure,
        oi_pressure=computed.oi_pressure,
        liquidation_pressure=computed.liquidation_pressure,
        skew_state=computed.skew_state,
        signal=computed.signal,
        regime=computed.regime,
        normalized_value=computed.normalized_value,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": row_count, "input_kind": data.kind, **computed.summary},
        input_profile=data.input_profile,
        used_fields=data.used_fields,
        warnings=data.warnings,
        diagnostics={"module": module_name, "indicator": indicator, **computed.diagnostics},
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "risk_state": report.risk_state, "direction": report.derivative_direction})],
        warnings=data.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _compute_futures(indicator: str, p: DerivativesParams, data: _DerivativesData) -> _ComputeOutput:
    price = _price_series(data, p)
    funding = _optional_series(data, "funding_rate")
    oi = _optional_series(data, "open_interest")
    volume = _optional_series(data, "volume")
    basis_rate = _basis_rate(data, p)
    premium = _premium_index(data)
    long_short = _optional_series(data, "long_short_ratio")
    taker = _optional_series(data, "taker_buy_sell_ratio")
    liq_long = _optional_series(data, "liquidation_long")
    liq_short = _optional_series(data, "liquidation_short")

    if indicator == "funding_rate":
        primary = _require_series(funding, "funding_rate")
    elif indicator == "funding_rate_zscore":
        primary = _zscore(_require_series(funding, "funding_rate"), int(p.window))
    elif indicator == "funding_momentum":
        primary = _require_series(funding, "funding_rate").diff(int(p.fast_window))
    elif indicator == "funding_regime":
        primary = _require_series(funding, "funding_rate")
    elif indicator == "funding_crowding_score":
        primary = _bounded_abs_zscore(_require_series(funding, "funding_rate"), int(p.regime_window))
    elif indicator == "open_interest_change":
        primary = _require_series(oi, "open_interest").diff()
    elif indicator == "open_interest_roc":
        primary = _require_series(oi, "open_interest").pct_change(fill_method=None) * 100.0
    elif indicator == "open_interest_zscore":
        primary = _zscore(_require_series(oi, "open_interest"), int(p.window))
    elif indicator == "price_oi_divergence":
        primary = _price_oi_divergence(_require_series(price, "price"), _require_series(oi, "open_interest"), int(p.window))
    elif indicator == "oi_volume_ratio":
        primary = _require_series(oi, "open_interest") / _require_series(volume, "volume").replace(0, np.nan)
    elif indicator == "basis_rate":
        primary = _require_series(basis_rate, "basis_rate")
    elif indicator == "basis_zscore":
        primary = _zscore(_require_series(basis_rate, "basis_rate"), int(p.window))
    elif indicator == "basis_momentum":
        primary = _require_series(basis_rate, "basis_rate").diff(int(p.fast_window))
    elif indicator == "premium_index":
        primary = _require_series(premium, "premium_index")
    elif indicator == "mark_index_deviation":
        primary = _mark_index_deviation(data)
    elif indicator == "perp_spot_deviation":
        primary = _perp_spot_deviation(data, p)
    elif indicator == "long_short_ratio":
        primary = _require_series(long_short, "long_short_ratio")
    elif indicator == "long_short_ratio_zscore":
        primary = _zscore(_require_series(long_short, "long_short_ratio"), int(p.window))
    elif indicator == "taker_buy_sell_ratio":
        primary = _require_series(taker, "taker_buy_sell_ratio")
    elif indicator == "taker_flow_imbalance":
        ratio = _require_series(taker, "taker_buy_sell_ratio")
        primary = (ratio - 1.0) / (ratio + 1.0).replace(0, np.nan) * 100.0
    elif indicator == "leverage_pressure_index":
        primary = _futures_pressure_index(funding, oi, basis_rate, long_short, p)
    elif indicator == "liquidation_imbalance":
        long_v = _require_series(liq_long, "liquidation_long")
        short_v = _require_series(liq_short, "liquidation_short")
        primary = (short_v - long_v) / (short_v + long_v).replace(0, np.nan) * 100.0
    elif indicator == "liquidation_pressure":
        primary = _liquidation_pressure(_require_series(liq_long, "liquidation_long"), _require_series(liq_short, "liquidation_short"), p)
    elif indicator == "long_liquidation_ratio":
        long_v = _require_series(liq_long, "liquidation_long")
        short_v = _require_series(liq_short, "liquidation_short")
        primary = long_v / (long_v + short_v).replace(0, np.nan) * 100.0
    elif indicator == "short_liquidation_ratio":
        long_v = _require_series(liq_long, "liquidation_long")
        short_v = _require_series(liq_short, "liquidation_short")
        primary = short_v / (long_v + short_v).replace(0, np.nan) * 100.0
    elif indicator == "liquidation_cascade_risk":
        total = _require_series(liq_long, "liquidation_long") + _require_series(liq_short, "liquidation_short")
        primary = _bounded_abs_zscore(total, int(p.regime_window))
    elif indicator == "derivatives_crowding_index":
        primary = _futures_pressure_index(funding, oi, basis_rate, long_short, p)
    elif indicator == "perp_risk_regime":
        primary = _futures_pressure_index(funding, oi, basis_rate, long_short, p)
    elif indicator == "futures_curve_pressure":
        primary = _zscore(_require_series(basis_rate, "basis_rate"), int(p.window))
    else:
        raise ValueError(f"unsupported futures indicator {indicator}")

    funding_pressure = _latest_pressure(funding, p)
    oi_pressure = _latest_pressure(oi, p)
    liquidation_pressure = _last_float(_liquidation_pressure(liq_long, liq_short, p)) if liq_long is not None and liq_short is not None else None
    leverage_pressure_series = _safe_futures_pressure_index(funding, oi, basis_rate, long_short, p)
    leverage_pressure = _last_float(leverage_pressure_series) if leverage_pressure_series is not None else None
    last = _last_float(primary)
    direction = _futures_direction(indicator, last)
    crowding = _crowding_state(funding, long_short, primary, p)
    risk = _risk_state(max(x for x in [leverage_pressure, liquidation_pressure, _abs_or_none(funding_pressure)] if x is not None) if any(x is not None for x in [leverage_pressure, liquidation_pressure, funding_pressure]) else None, p)
    term = _term_structure_state(_last_float(basis_rate))
    series = {"value": primary}
    for name, ser in (("price", price), ("funding_rate", funding), ("open_interest", oi), ("basis_rate", basis_rate), ("premium_index", premium), ("long_short_ratio", long_short), ("taker_buy_sell_ratio", taker), ("liquidation_long", liq_long), ("liquidation_short", liq_short)):
        if ser is not None:
            series[name] = ser
    return _ComputeOutput(
        primary=primary,
        series=series,
        derivative_direction=direction,
        risk_state=risk,
        crowding_state=crowding,
        term_structure_state=term,
        leverage_pressure=leverage_pressure,
        funding_pressure=funding_pressure,
        oi_pressure=oi_pressure,
        liquidation_pressure=liquidation_pressure,
        signal=_signal_from_state(direction, risk, crowding),
        regime=risk,
        normalized_value=_normalized(primary, p),
        summary={"calculation": indicator},
    )


def _compute_options(indicator: str, p: DerivativesParams, data: _DerivativesData) -> _ComputeOutput:
    chain = _option_chain(data)
    atm_iv = _atm_iv_series(chain)
    put_iv, call_iv = _atm_put_call_iv(chain)
    put_volume, call_volume = _option_sum_by_type(chain, "volume")
    put_oi, call_oi = _option_sum_by_type(chain, "open_interest")
    underlying = _option_underlying(chain)

    if indicator == "implied_volatility":
        primary = atm_iv
    elif indicator == "iv_rank":
        primary = (atm_iv - atm_iv.rolling(int(p.regime_window), min_periods=int(p.window)).min()) / (atm_iv.rolling(int(p.regime_window), min_periods=int(p.window)).max() - atm_iv.rolling(int(p.regime_window), min_periods=int(p.window)).min()).replace(0, np.nan) * 100.0
    elif indicator == "iv_percentile":
        primary = _rolling_percentile(atm_iv, int(p.regime_window))
    elif indicator == "iv_term_structure":
        near, far = _near_far_iv(chain, p)
        primary = far - near
    elif indicator == "front_back_iv_spread":
        near, far = _near_far_iv(chain, p)
        primary = near - far
    elif indicator == "put_call_iv_skew":
        primary = put_iv - call_iv
    elif indicator == "risk_reversal":
        primary = call_iv - put_iv
    elif indicator == "butterfly_skew":
        primary = ((put_iv + call_iv) / 2.0) - atm_iv
    elif indicator == "smile_curvature":
        primary = ((put_iv + call_iv) / 2.0) - atm_iv
    elif indicator == "atm_iv_skew":
        primary = put_iv - call_iv
    elif indicator == "put_call_volume_ratio":
        primary = put_volume / call_volume.replace(0, np.nan)
    elif indicator == "put_call_open_interest_ratio":
        primary = put_oi / call_oi.replace(0, np.nan)
    elif indicator == "option_volume_oi_ratio":
        primary = (put_volume + call_volume) / (put_oi + call_oi).replace(0, np.nan)
    elif indicator == "gamma_exposure":
        primary = _greek_exposure(chain, "gamma", underlying, power=2.0)
    elif indicator == "delta_exposure":
        primary = _greek_exposure(chain, "delta", underlying, power=1.0)
    elif indicator == "vega_exposure":
        primary = _greek_exposure(chain, "vega", underlying, power=0.0)
    elif indicator == "theta_exposure":
        primary = _greek_exposure(chain, "theta", underlying, power=0.0)
    elif indicator == "dealer_gamma_proxy":
        primary = -_greek_exposure(chain, "gamma", underlying, power=2.0)
    elif indicator == "options_crowding_index":
        primary = _options_crowding_index(atm_iv, put_oi, call_oi, put_volume, call_volume, p)
    elif indicator == "volatility_risk_premium_proxy":
        rv = _realized_volatility_proxy(chain, underlying, p)
        primary = atm_iv - rv
    elif indicator == "max_pain_proxy":
        primary = _max_pain(chain)
    else:
        raise ValueError(f"unsupported options indicator {indicator}")

    skew_value = _last_float(put_iv - call_iv)
    skew_state = "put_skew" if skew_value is not None and skew_value > 0 else "call_skew" if skew_value is not None and skew_value < 0 else "flat"
    last = _last_float(primary)
    risk = _risk_state(_normalized(primary, p), p)
    direction = _options_direction(indicator, last)
    term = "inverted" if indicator in {"iv_term_structure", "front_back_iv_spread"} and last is not None and last < 0 else "normal" if indicator in {"iv_term_structure", "front_back_iv_spread"} else "unknown"
    series = {"value": primary, "atm_iv": atm_iv}
    for name, ser in (("put_iv", put_iv), ("call_iv", call_iv), ("put_volume", put_volume), ("call_volume", call_volume), ("put_open_interest", put_oi), ("call_open_interest", call_oi), ("underlying_price", underlying)):
        if ser is not None:
            series[name] = ser
    diagnostics: Dict[str, Any] = {}
    if indicator in {"dealer_gamma_proxy", "volatility_risk_premium_proxy", "max_pain_proxy"}:
        diagnostics["proxy"] = True
        diagnostics["proxy_note"] = f"{indicator} is a diagnostic proxy from caller-supplied option-chain fields, not true dealer inventory or model-implied fair value."
    return _ComputeOutput(
        primary=primary,
        series=series,
        derivative_direction=direction,
        risk_state=risk,
        crowding_state=_option_crowding_state(put_oi, call_oi, primary, p),
        term_structure_state=term,
        leverage_pressure=None,
        funding_pressure=None,
        oi_pressure=_latest_pressure(put_oi + call_oi, p),
        liquidation_pressure=None,
        skew_state=skew_state,
        signal=_signal_from_state(direction, risk, skew_state),
        regime=risk,
        normalized_value=_normalized(primary, p),
        summary={"calculation": indicator},
        diagnostics=diagnostics,
    )


def _validate_params(p: DerivativesParams) -> Optional[ModuleResult[Any]]:
    for name in ("window", "fast_window", "slow_window", "regime_window", "term_structure_near_days", "term_structure_far_days", "periods_per_year"):
        try:
            value = int(getattr(p, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if int(p.fast_window) >= int(p.slow_window):
        return ModuleResult.fail("invalid_parameter", "fast_window must be smaller than slow_window", field="fast_window")
    for name in ("high_percentile", "low_percentile", "crowding_threshold", "liquidation_threshold"):
        value = _safe_float(getattr(p, name))
        if value is None or value < 0.0 or value > 100.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be between 0 and 100", field=name)
    if float(p.low_percentile) >= float(p.high_percentile):
        return ModuleResult.fail("invalid_parameter", "low_percentile must be below high_percentile", field="low_percentile")
    if _safe_float(p.extreme_zscore) is None or float(p.extreme_zscore) <= 0.0:
        return ModuleResult.fail("invalid_parameter", "extreme_zscore must be positive", field="extreme_zscore")
    return None


def _missing_required_fields(indicator: str, data: _DerivativesData) -> List[str]:
    used = data.used_fields
    req: Dict[str, List[str]] = {
        "funding_rate": ["funding_rate"],
        "funding_rate_zscore": ["funding_rate"],
        "funding_momentum": ["funding_rate"],
        "funding_regime": ["funding_rate"],
        "funding_crowding_score": ["funding_rate"],
        "open_interest_change": ["open_interest"],
        "open_interest_roc": ["open_interest"],
        "open_interest_zscore": ["open_interest"],
        "price_oi_divergence": ["open_interest", "price"],
        "oi_volume_ratio": ["open_interest", "volume"],
        "basis_rate": [],
        "basis_zscore": [],
        "basis_momentum": [],
        "premium_index": [],
        "mark_index_deviation": ["mark_price", "index_price"],
        "perp_spot_deviation": ["spot_price"],
        "long_short_ratio": ["long_short_ratio"],
        "long_short_ratio_zscore": ["long_short_ratio"],
        "taker_buy_sell_ratio": ["taker_buy_sell_ratio"],
        "taker_flow_imbalance": ["taker_buy_sell_ratio"],
        "leverage_pressure_index": ["open_interest"],
        "liquidation_imbalance": ["liquidation_long", "liquidation_short"],
        "liquidation_pressure": ["liquidation_long", "liquidation_short"],
        "long_liquidation_ratio": ["liquidation_long", "liquidation_short"],
        "short_liquidation_ratio": ["liquidation_long", "liquidation_short"],
        "liquidation_cascade_risk": ["liquidation_long", "liquidation_short"],
        "derivatives_crowding_index": ["open_interest"],
        "perp_risk_regime": ["open_interest"],
        "futures_curve_pressure": [],
    }
    option_base = ["ts", "option_type", "strike", "expiry", "underlying_price", "mark_iv"]
    option_oi = ["open_interest"]
    option_volume = ["volume"]
    option_greeks = {
        "gamma_exposure": ["gamma", "open_interest"],
        "delta_exposure": ["delta", "open_interest"],
        "vega_exposure": ["vega", "open_interest"],
        "theta_exposure": ["theta", "open_interest"],
        "dealer_gamma_proxy": ["gamma", "open_interest"],
    }
    if indicator in OPTIONS_INDICATORS:
        required = list(option_base)
        if indicator in {"put_call_volume_ratio", "option_volume_oi_ratio", "options_crowding_index"}:
            required += option_volume
        if indicator in {"put_call_open_interest_ratio", "option_volume_oi_ratio", "options_crowding_index", "max_pain_proxy"}:
            required += option_oi
        required += option_greeks.get(indicator, [])
        return [name for name in dict.fromkeys(required) if name not in used]
    required = req.get(indicator, [])
    missing = [name for name in required if name not in used]
    if indicator in {"basis_rate", "basis_zscore", "basis_momentum", "futures_curve_pressure"} and "basis" not in used and not (("price" in used or "mark_price" in used) and ("spot_price" in used or "index_price" in used)):
        missing.append("basis or price/mark_price plus spot_price/index_price")
    if indicator == "premium_index" and "premium" not in used and not ("mark_price" in used and "index_price" in used):
        missing.append("premium or mark_price plus index_price")
    if indicator == "perp_spot_deviation" and "price" not in used and "mark_price" not in used:
        missing.append("price or mark_price")
    return missing


def _minimum_rows(indicator: str, p: DerivativesParams) -> int:
    if indicator in OPTIONS_INDICATORS:
        if indicator in {"iv_rank", "iv_percentile", "options_crowding_index", "volatility_risk_premium_proxy"}:
            return int(p.window)
        return 1
    if indicator.endswith("_zscore") or indicator in {"funding_crowding_score", "liquidation_cascade_risk", "derivatives_crowding_index", "perp_risk_regime"}:
        return int(p.window)
    if indicator in {"funding_momentum", "basis_momentum", "price_oi_divergence"}:
        return int(p.window)
    return 2


def _time_row_count(data: _DerivativesData) -> int:
    return int(data.frame["__ts"].nunique())


def _time_series(data: _DerivativesData, logical: str, agg: str = "last") -> Optional[pd.Series]:
    col = data.used_fields.get(logical)
    if col is None:
        return None
    grouped = data.frame.groupby("__ts", sort=True)[col]
    if agg == "sum":
        out = grouped.sum(min_count=1)
    elif agg == "mean":
        out = grouped.mean()
    else:
        out = grouped.last()
    return pd.to_numeric(out, errors="coerce")


def _optional_series(data: _DerivativesData, logical: str) -> Optional[pd.Series]:
    return _time_series(data, logical)


def _require_series(series: Optional[pd.Series], name: str) -> pd.Series:
    if series is None or series.dropna().empty:
        raise ValueError(f"{name} has no usable numeric values")
    return series


def _price_series(data: _DerivativesData, p: DerivativesParams) -> Optional[pd.Series]:
    for logical in ("price", "mark_price", "index_price", "spot_price", "underlying_price"):
        ser = _time_series(data, logical)
        if ser is not None and not ser.dropna().empty:
            return ser
    return None


def _basis_rate(data: _DerivativesData, p: DerivativesParams) -> Optional[pd.Series]:
    basis = _time_series(data, "basis")
    if basis is not None and not basis.dropna().empty:
        ref = _first_series(_time_series(data, "spot_price"), _time_series(data, "index_price"), _price_series(data, p))
        if ref is not None and not ref.dropna().empty:
            return basis / ref.replace(0, np.nan) * 100.0
        return basis
    contract = _first_series(_time_series(data, "price"), _time_series(data, "mark_price"))
    ref = _first_series(_time_series(data, "spot_price"), _time_series(data, "index_price"))
    if contract is None or ref is None:
        return None
    return (contract - ref) / ref.replace(0, np.nan) * 100.0


def _premium_index(data: _DerivativesData) -> Optional[pd.Series]:
    premium = _time_series(data, "premium")
    if premium is not None and not premium.dropna().empty:
        return premium
    mark = _time_series(data, "mark_price")
    index = _time_series(data, "index_price")
    if mark is None or index is None or mark.dropna().empty or index.dropna().empty:
        return None
    return (mark - index) / index.replace(0, np.nan) * 100.0


def _mark_index_deviation(data: _DerivativesData) -> pd.Series:
    mark = _require_series(_time_series(data, "mark_price"), "mark_price")
    index = _require_series(_time_series(data, "index_price"), "index_price")
    return (mark - index) / index.replace(0, np.nan) * 100.0


def _perp_spot_deviation(data: _DerivativesData, p: DerivativesParams) -> pd.Series:
    contract = _require_series(_first_series(_time_series(data, "mark_price"), _time_series(data, "price")), "price or mark_price")
    spot = _require_series(_time_series(data, "spot_price"), "spot_price")
    return (contract - spot) / spot.replace(0, np.nan) * 100.0


def _first_series(*series: Optional[pd.Series]) -> Optional[pd.Series]:
    for ser in series:
        if ser is not None and not ser.dropna().empty:
            return ser
    return None


def _zscore(series: pd.Series, n: int) -> pd.Series:
    mean = series.rolling(n, min_periods=n).mean()
    std = series.rolling(n, min_periods=n).std(ddof=0).replace(0, np.nan)
    return (series - mean) / std


def _bounded_abs_zscore(series: pd.Series, n: int) -> pd.Series:
    return _zscore(series, n).abs().clip(upper=5.0) / 5.0 * 100.0


def _price_oi_divergence(price: pd.Series, oi: pd.Series, n: int) -> pd.Series:
    p_mom = price.pct_change(n, fill_method=None)
    oi_mom = oi.pct_change(n, fill_method=None)
    out = pd.Series(0.0, index=price.index)
    out[(p_mom > 0) & (oi_mom < 0)] = -1.0
    out[(p_mom < 0) & (oi_mom > 0)] = 1.0
    out[(p_mom > 0) & (oi_mom > 0)] = 0.5
    out[(p_mom < 0) & (oi_mom < 0)] = -0.5
    return out


def _liquidation_pressure(long_v: Optional[pd.Series], short_v: Optional[pd.Series], p: DerivativesParams) -> pd.Series:
    total = _require_series(long_v, "liquidation_long") + _require_series(short_v, "liquidation_short")
    return _bounded_abs_zscore(total, int(p.regime_window))


def _futures_pressure_index(funding: Optional[pd.Series], oi: Optional[pd.Series], basis: Optional[pd.Series], long_short: Optional[pd.Series], p: DerivativesParams) -> pd.Series:
    parts = []
    for ser in (funding, oi, basis, long_short):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(_bounded_abs_zscore(ser, int(p.window)))
    if not parts:
        raise ValueError("not enough fields to compute futures pressure")
    return pd.concat(parts, axis=1).mean(axis=1)


def _safe_futures_pressure_index(funding: Optional[pd.Series], oi: Optional[pd.Series], basis: Optional[pd.Series], long_short: Optional[pd.Series], p: DerivativesParams) -> Optional[pd.Series]:
    try:
        return _futures_pressure_index(funding, oi, basis, long_short, p)
    except Exception:
        return None


def _option_chain(data: _DerivativesData) -> pd.DataFrame:
    if data.kind != "options":
        raise ValueError("option indicator requires option-chain long rows")
    frame = data.frame.copy()
    for logical in (
        "strike",
        "underlying_price",
        "mark_iv",
        "open_interest",
        "volume",
        "delta",
        "gamma",
        "vega",
        "theta",
        "realized_volatility",
    ):
        if logical in data.used_fields:
            frame[f"__{logical}"] = pd.to_numeric(frame[data.used_fields[logical]], errors="coerce")
    if frame["__option_type"].isna().any():
        raise ValueError("option_type must be call/put or c/p")
    return frame


def _option_underlying(chain: pd.DataFrame) -> pd.Series:
    return chain.groupby("__ts", sort=True)["__underlying_price"].median()


def _atm_iv_series(chain: pd.DataFrame) -> pd.Series:
    rows = []
    for ts, grp in chain.groupby("__ts", sort=True):
        rows.append((ts, _atm_iv_for_group(grp)))
    return pd.Series({ts: val for ts, val in rows}, dtype=float)


def _atm_iv_for_group(grp: pd.DataFrame) -> float:
    if "__mark_iv" not in grp or "__strike" not in grp or "__underlying_price" not in grp:
        return np.nan
    underlying = float(grp["__underlying_price"].median())
    atm = grp.iloc[(grp["__strike"] - underlying).abs().argsort()[: max(2, min(4, len(grp)))]]
    return float(atm["__mark_iv"].mean())


def _atm_put_call_iv(chain: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    put_vals: Dict[Any, float] = {}
    call_vals: Dict[Any, float] = {}
    for ts, grp in chain.groupby("__ts", sort=True):
        underlying = float(grp["__underlying_price"].median())
        for opt_type, store in (("put", put_vals), ("call", call_vals)):
            sub = grp[grp["__option_type"] == opt_type]
            if sub.empty:
                store[ts] = np.nan
                continue
            atm = sub.iloc[(sub["__strike"] - underlying).abs().argsort()[: max(1, min(3, len(sub)))]]
            store[ts] = float(atm["__mark_iv"].mean())
    return pd.Series(put_vals, dtype=float), pd.Series(call_vals, dtype=float)


def _near_far_iv(chain: pd.DataFrame, p: DerivativesParams) -> Tuple[pd.Series, pd.Series]:
    near_vals: Dict[Any, float] = {}
    far_vals: Dict[Any, float] = {}
    for ts, grp in chain.groupby("__ts", sort=True):
        dte = (grp["__expiry"] - ts).dt.total_seconds() / 86400.0
        near = grp.iloc[(dte - float(p.term_structure_near_days)).abs().argsort()[: max(2, min(4, len(grp)))]]
        far = grp.iloc[(dte - float(p.term_structure_far_days)).abs().argsort()[: max(2, min(4, len(grp)))]]
        near_vals[ts] = float(near["__mark_iv"].mean())
        far_vals[ts] = float(far["__mark_iv"].mean())
    return pd.Series(near_vals, dtype=float), pd.Series(far_vals, dtype=float)


def _option_sum_by_type(chain: pd.DataFrame, logical: str) -> Tuple[pd.Series, pd.Series]:
    col = f"__{logical}"
    if col not in chain:
        empty = pd.Series(index=sorted(chain["__ts"].unique()), dtype=float)
        return empty, empty
    grouped = chain.groupby(["__ts", "__option_type"], sort=True)[col].sum(min_count=1).unstack()
    put = grouped["put"] if "put" in grouped else pd.Series(index=grouped.index, dtype=float)
    call = grouped["call"] if "call" in grouped else pd.Series(index=grouped.index, dtype=float)
    return put, call


def _greek_exposure(chain: pd.DataFrame, greek: str, underlying: pd.Series, *, power: float) -> pd.Series:
    greek_col = f"__{greek}"
    if greek_col not in chain or "__open_interest" not in chain:
        raise ValueError(f"{greek} exposure requires {greek} and open_interest")
    base = chain[greek_col] * chain["__open_interest"].fillna(0.0)
    if power == 1.0:
        base = base * chain["__underlying_price"]
    elif power == 2.0:
        base = base * (chain["__underlying_price"] ** 2)
    return base.groupby(chain["__ts"], sort=True).sum(min_count=1)


def _options_crowding_index(atm_iv: pd.Series, put_oi: pd.Series, call_oi: pd.Series, put_volume: pd.Series, call_volume: pd.Series, p: DerivativesParams) -> pd.Series:
    iv_part = _rolling_percentile(atm_iv, int(p.regime_window))
    oi_ratio = put_oi / call_oi.replace(0, np.nan)
    vol_ratio = put_volume / call_volume.replace(0, np.nan)
    ratio_part = _bounded_abs_zscore(oi_ratio.fillna(1.0), int(p.window))
    vol_part = _bounded_abs_zscore(vol_ratio.fillna(1.0), int(p.window))
    return pd.concat([iv_part, ratio_part, vol_part], axis=1).mean(axis=1)


def _realized_volatility_proxy(chain: pd.DataFrame, underlying: pd.Series, p: DerivativesParams) -> pd.Series:
    if "__realized_volatility" in chain:
        return chain.groupby("__ts", sort=True)["__realized_volatility"].median()
    returns = underlying.pct_change(fill_method=None)
    return returns.rolling(int(p.window), min_periods=int(p.window)).std(ddof=0) * math.sqrt(float(p.periods_per_year))


def _max_pain(chain: pd.DataFrame) -> pd.Series:
    vals: Dict[Any, float] = {}
    for ts, grp in chain.groupby("__ts", sort=True):
        strikes = sorted(float(x) for x in grp["__strike"].dropna().unique())
        if not strikes or "__open_interest" not in grp:
            vals[ts] = np.nan
            continue
        losses = []
        for settle in strikes:
            call_loss = ((max(0.0, settle - float(row["__strike"])) * float(row.get("__open_interest", 0.0) or 0.0)) for _, row in grp[grp["__option_type"] == "call"].iterrows())
            put_loss = ((max(0.0, float(row["__strike"]) - settle) * float(row.get("__open_interest", 0.0) or 0.0)) for _, row in grp[grp["__option_type"] == "put"].iterrows())
            losses.append((sum(call_loss) + sum(put_loss), settle))
        vals[ts] = min(losses)[1]
    return pd.Series(vals, dtype=float)


def _rolling_percentile(series: pd.Series, n: int) -> pd.Series:
    def calc(x: np.ndarray) -> float:
        valid = x[~np.isnan(x)]
        if len(valid) == 0:
            return np.nan
        return float((valid <= valid[-1]).sum() / len(valid) * 100.0)
    return series.rolling(n, min_periods=min(n, max(2, n // 4))).apply(calc, raw=True)


def _latest_pressure(series: Optional[pd.Series], p: DerivativesParams) -> Optional[float]:
    if series is None or len(series.dropna()) < int(p.window):
        return None
    return _last_float(_bounded_abs_zscore(series, int(p.window)))


def _normalized(series: pd.Series, p: DerivativesParams) -> Optional[float]:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < max(2, min(int(p.window), len(valid))):
        return None
    last = float(valid.iloc[-1])
    return float((valid <= last).sum() / len(valid) * 100.0)


def _risk_state(value: Optional[float], p: DerivativesParams) -> str:
    if value is None:
        return "unknown"
    if value >= float(p.crowding_threshold):
        return "high"
    if value <= float(p.low_percentile):
        return "low"
    return "normal"


def _crowding_state(funding: Optional[pd.Series], long_short: Optional[pd.Series], primary: pd.Series, p: DerivativesParams) -> str:
    funding_last = _last_float(funding) if funding is not None else None
    ls_last = _last_float(long_short) if long_short is not None else None
    if funding_last is not None and funding_last > 0 and (ls_last is None or ls_last >= 1.0):
        return "crowded_long"
    if funding_last is not None and funding_last < 0 and (ls_last is None or ls_last <= 1.0):
        return "crowded_short"
    return "neutral"


def _option_crowding_state(put_oi: pd.Series, call_oi: pd.Series, primary: pd.Series, p: DerivativesParams) -> str:
    ratio = _last_float(put_oi / call_oi.replace(0, np.nan))
    if ratio is None:
        return "unknown"
    if ratio > 1.2:
        return "put_crowded"
    if ratio < 0.8:
        return "call_crowded"
    return "neutral"


def _term_structure_state(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value > 0:
        return "contango"
    if value < 0:
        return "backwardation"
    return "flat"


def _futures_direction(indicator: str, value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if indicator in {"long_liquidation_ratio", "new_lows"}:
        return "bearish" if value > 50 else "neutral"
    if value > 0:
        return "bullish"
    if value < 0:
        return "bearish"
    return "neutral"


def _options_direction(indicator: str, value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if indicator in {"put_call_iv_skew", "put_call_volume_ratio", "put_call_open_interest_ratio"}:
        return "bearish" if value > 0 else "bullish" if value < 0 else "neutral"
    if value > 0:
        return "bullish"
    if value < 0:
        return "bearish"
    return "neutral"


def _signal_from_state(direction: str, risk: str, crowding: str) -> str:
    if risk in {"high", "extreme"}:
        return "risk_elevated"
    if crowding not in {"neutral", "unknown"}:
        return crowding
    return direction if direction != "unknown" else "none"


def _raw_to_frame(raw: Any, extractor: Optional[ExtractorSpec]) -> ModuleResult[pd.DataFrame]:
    try:
        if extractor and extractor.extractors:
            data = {name: fn(raw) for name, fn in extractor.extractors.items()}
            return ModuleResult.success(pd.DataFrame(data))
        if isinstance(raw, pd.DataFrame):
            return ModuleResult.success(raw.copy())
        if isinstance(raw, pd.Series):
            return ModuleResult.success(pd.DataFrame({str(raw.name or "value"): raw.to_list()}))
        if isinstance(raw, dict):
            return ModuleResult.success(pd.DataFrame(raw))
        if isinstance(raw, (list, tuple)):
            if len(raw) == 0:
                return ModuleResult.fail("empty_input", "input sequence is empty")
            if isinstance(raw[0], dict):
                return ModuleResult.success(pd.DataFrame(list(raw)))
            return ModuleResult.success(pd.DataFrame(raw))
    except Exception as exc:
        return ModuleResult.fail("invalid_input", "could not convert derivatives input to DataFrame", details={"error": str(exc)})
    if isinstance(raw, IterableABC) and not isinstance(raw, (str, bytes)):
        try:
            return ModuleResult.success(pd.DataFrame(list(raw)))
        except Exception:
            pass
    return ModuleResult.fail("unsupported_input", f"unsupported input type: {type(raw).__name__}; provide DataFrame, Series, list, dict, or ExtractorSpec")


def _find_col(cols: Dict[str, Any], name: str) -> Optional[Any]:
    if name in cols:
        return cols[name]
    lower = {str(k).lower(): v for k, v in cols.items()}
    return lower.get(str(name).lower())


def _find_any_col(cols: Dict[str, Any], names: List[str]) -> Optional[Any]:
    for name in names:
        col = _find_col(cols, name)
        if col is not None:
            return col
    return None


def _normalize_option_type(value: str) -> Optional[str]:
    raw = str(value).lower().strip()
    if raw in {"c", "call", "calls"}:
        return "call"
    if raw in {"p", "put", "puts"}:
        return "put"
    return None


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series.tolist()]


def _last_float(series: Optional[pd.Series]) -> Optional[float]:
    if series is None:
        return None
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return None
    value = float(valid.iloc[-1])
    return value if math.isfinite(value) else None


def _safe_float(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def _abs_or_none(value: Optional[float]) -> Optional[float]:
    return None if value is None else abs(float(value))


__all__ = ["DerivativesParams", "DerivativesReport", "normalize_derivatives_input", "run_derivatives_indicator"]
