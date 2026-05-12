"""
quant_strategy_tokenizer.indicators.structure_common
====================================================
Purpose: shared implementation layer for atomic price-structure indicator
tokens.
Core idea: Normalize caller-supplied price/OHLC/OHLCV data, extract swings,
cluster nearby levels, detect breaks, retests, ranges, gaps, sweeps, and
profile approximations, then return a uniform StructureReport. Assumes
structure tokens should expose inspectable levels and zones without owning
data sourcing, execution, or order-flow claims.
Inputs: raw user data, DataFrameSpec/ExtractorSpec, StructureParams-compatible
configuration, indicator name, input kind, and ModuleRunContext.
Outputs: StructureReport wrapped in ModuleResult with latest values, structure
bias/state, support/resistance fields, structured levels/zones, optional series,
diagnostics, warnings, and report files when requested.
Failure semantics: invalid params, missing fields, insufficient history, flat
price where structure cannot be inferred, invalid profile bins, and calculation
errors return ModuleResult.fail.
Market generalization: all calculations operate on caller-mapped numeric fields
and do not assume asset class, venue, session model, quote currency, order book,
tick data, or symbol format.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class StructureParams:
    """Generic structure-indicator options used by atomic wrapper modules.

    Configuration:
    - `value_field`, `volume_field`: logical price and volume fields resolved
      through DataFrameSpec.
    - `window`, `left_bars`, `right_bars`, `lookback`: local-structure
      lookbacks in rows/bars.
    - `tolerance_pct`, `zone_width_pct`, `breakout_buffer_pct`, `min_gap_pct`,
      `swing_threshold_pct`: fractional thresholds, e.g. 0.003 means 0.3%.
    - `min_touches`, `max_levels`: level clustering and filtering controls.
    - `profile_bins`, `value_area_pct`: OHLCV profile approximation controls.
    """

    value_field: str = "close"
    volume_field: str = "volume"
    window: int = 20
    left_bars: int = 3
    right_bars: int = 3
    lookback: int = 120
    tolerance_pct: float = 0.003
    min_touches: int = 2
    max_levels: int = 8
    zone_width_pct: float = 0.005
    breakout_buffer_pct: float = 0.002
    retest_bars: int = 10
    profile_bins: int = 24
    value_area_pct: float = 70.0
    min_gap_pct: float = 0.001
    swing_threshold_pct: float = 0.02


@dataclass
class StructureReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    structure_bias: str = "unknown"
    structure_state: str = "unknown"
    nearest_support: Optional[float] = None
    nearest_resistance: Optional[float] = None
    distance_to_support: Optional[float] = None
    distance_to_resistance: Optional[float] = None
    levels: List[Dict[str, Any]] = field(default_factory=list)
    zones: List[Dict[str, Any]] = field(default_factory=list)
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
class _ComputeOutput:
    primary: pd.Series
    series: Dict[str, pd.Series]
    levels: List[Dict[str, Any]] = field(default_factory=list)
    zones: List[Dict[str, Any]] = field(default_factory=list)
    structure_bias: str = "unknown"
    structure_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_structure_input(request: Any, input_kind: str) -> ModuleResult[Any]:
    params = request.params
    value_field = str(getattr(params, "value_field", "close") or "close")
    volume_field = str(getattr(params, "volume_field", "volume") or "volume")
    if input_kind == "price":
        primary = normalize_frame(request.data, required_fields=[value_field], optional_fields=[], spec=request.spec, extractor=request.extractor)
        if primary.ok:
            return primary
        fallback = normalize_frame(request.data, required_fields=["value"], optional_fields=[], spec=request.spec, extractor=request.extractor)
        if fallback.ok and fallback.value is not None:
            fallback.value.used_fields[value_field] = fallback.value.used_fields["value"]
            fallback.value.used_fields["close"] = fallback.value.used_fields["value"]
            fallback.value.warnings.append("price field was inferred from value column")
            return fallback
        return primary
    if input_kind == "ohlcv":
        required = ["high", "low", "close", volume_field]
        optional = ["open"]
    elif input_kind == "ohlc_open":
        required = ["open", "high", "low", "close"]
        optional = [volume_field]
    else:
        required = ["high", "low", "close"]
        optional = ["open", volume_field]
    return normalize_frame(request.data, required_fields=required, optional_fields=optional, spec=request.spec, extractor=request.extractor)


def run_structure_indicator(indicator: str, request: Any, *, input_kind: str, module_name: str) -> ModuleResult[StructureReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error

    norm = normalize_structure_input(request, input_kind)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")

    frame = nf.frame
    used = dict(nf.used_fields)
    close_col = used.get(str(params.value_field)) or used.get("close") or used.get("value")
    if close_col is None:
        return ModuleResult.fail("missing_required_field", "structure indicator needs a resolved close/value field")
    close = pd.to_numeric(frame[close_col], errors="coerce")
    high = pd.to_numeric(frame[used["high"]], errors="coerce") if "high" in used else close
    low = pd.to_numeric(frame[used["low"]], errors="coerce") if "low" in used else close
    open_ = pd.to_numeric(frame[used["open"]], errors="coerce") if "open" in used else close
    volume_col = used.get(str(params.volume_field)) or used.get("volume")
    volume = pd.to_numeric(frame[volume_col], errors="coerce") if volume_col is not None else None

    min_rows = _minimum_rows(indicator, params)
    numeric_rows = int(close.dropna().shape[0])
    if numeric_rows < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} numeric rows, got {numeric_rows}")
    if indicator not in _FLAT_OK and _is_flat(close):
        return ModuleResult.fail("insufficient_data", "price is flat; structure cannot be inferred")

    try:
        computed = _compute_native(indicator, params, open_, high, low, close, volume)
    except Exception as exc:
        return ModuleResult.fail(
            "calculation_error",
            f"{indicator} calculation failed",
            details={"error": str(exc), "error_type": type(exc).__name__},
        )

    primary = computed.primary.replace([np.inf, -np.inf], np.nan)
    last = _last_float(primary)
    if last is None:
        return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output")

    series_map = {name: ser.replace([np.inf, -np.inf], np.nan) for name, ser in computed.series.items()}
    if "value" not in series_map:
        series_map["value"] = primary
    last_values = {name: _last_float(ser) for name, ser in series_map.items()}
    nearest_support, nearest_resistance = _nearest_levels(close, computed.levels)
    last_close = _last_float(close)
    distance_support = _distance(last_close, nearest_support)
    distance_resistance = _distance(last_close, nearest_resistance)

    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = StructureReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        structure_bias=computed.structure_bias,
        structure_state=computed.structure_state,
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        distance_to_support=distance_support,
        distance_to_resistance=distance_resistance,
        levels=computed.levels,
        zones=computed.zones,
        signal=computed.signal,
        regime=computed.regime,
        normalized_value=computed.normalized_value,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": int(len(close)), "input_kind": input_kind, **computed.summary},
        input_profile=nf.input_profile,
        used_fields=used,
        missing_fields=nf.missing_fields,
        warnings=nf.warnings,
        diagnostics={
            "module": module_name,
            "indicator": indicator,
            "value_col": str(close_col),
            "volume_col": "" if volume_col is None else str(volume_col),
            **computed.diagnostics,
        },
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "state": report.structure_state, "bias": report.structure_bias})],
        warnings=nf.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _validate_params(params: StructureParams) -> Optional[ModuleResult[Any]]:
    for name in ("window", "left_bars", "right_bars", "lookback", "min_touches", "max_levels", "retest_bars", "profile_bins"):
        try:
            value = int(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    for name in ("tolerance_pct", "zone_width_pct", "breakout_buffer_pct", "value_area_pct", "min_gap_pct", "swing_threshold_pct"):
        try:
            value = float(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)
        if value < 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be non-negative", field=name)
    if int(params.profile_bins) < 2:
        return ModuleResult.fail("invalid_parameter", "profile_bins must be at least 2", field="profile_bins")
    if not (0.0 < float(params.value_area_pct) <= 100.0):
        return ModuleResult.fail("invalid_parameter", "value_area_pct must satisfy 0 < value <= 100", field="value_area_pct")
    return None


_FLAT_OK = {"inside_bar", "outside_bar", "price_gap", "fair_value_gap"}


def _minimum_rows(indicator: str, p: StructureParams) -> int:
    if indicator in {"inside_bar", "outside_bar", "price_gap", "fair_value_gap"}:
        return 3
    if indicator in {"market_structure_shift", "break_of_structure", "change_of_character", "zigzag_structure"}:
        return max(int(p.left_bars) + int(p.right_bars) + 3, int(p.window) + 2)
    if indicator in {"volume_profile", "market_profile", "point_of_control", "value_area", "profile_acceptance"}:
        return max(10, min(int(p.lookback), 30))
    return max(int(p.window), int(p.left_bars) + int(p.right_bars) + 2, 5)


def _compute_native(indicator: str, p: StructureParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: Optional[pd.Series]) -> _ComputeOutput:
    if indicator in {"swing_points", "fractal_pivots"}:
        return _swing_output(indicator, high, low, close, p)
    if indicator == "zigzag_structure":
        return _zigzag(high, low, close, p)
    if indicator == "higher_high_lower_low":
        return _hhll(high, low, close, p)
    if indicator in {"market_structure_shift", "break_of_structure", "change_of_character"}:
        return _structure_break(indicator, high, low, close, p)
    if indicator == "trendline_structure":
        return _trendline_structure(close, p)
    if indicator == "pivot_points":
        return _pivot_points(high, low, close, p)
    if indicator in {"rolling_support_resistance", "support_resistance_zones", "nearest_support_resistance", "level_touch_count"}:
        return _support_resistance(indicator, high, low, close, p)
    if indicator in {"breakout_detector", "retest_detector", "false_breakout_detector"}:
        return _breakout_family(indicator, high, low, close, p)
    if indicator in {"range_box", "consolidation_zone", "range_position", "range_breakout_strength"}:
        return _range_family(indicator, high, low, close, p)
    if indicator in {"inside_bar", "outside_bar", "narrow_range", "wide_range"}:
        return _bar_range_family(indicator, high, low, close, p)
    if indicator in {"price_gap", "fair_value_gap"}:
        return _gap_family(indicator, open_, high, low, close, p)
    if indicator in {"liquidity_sweep", "equal_highs_lows"}:
        return _liquidity_family(indicator, high, low, close, p)
    if indicator in {"order_block_proxy", "supply_demand_zone"}:
        return _zone_proxy(indicator, open_, high, low, close, volume, p)
    if indicator in {"volume_profile", "market_profile", "point_of_control", "value_area", "profile_acceptance"}:
        return _profile_family(indicator, high, low, close, volume, p)
    raise ValueError(f"unsupported indicator {indicator}")


def _swing_output(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    swing_high, swing_low = _swing_masks(high, low, int(p.left_bars), int(p.right_bars))
    value = pd.Series(0.0, index=close.index)
    value[swing_high] = 1.0
    value[swing_low] = -1.0
    levels = _levels_from_swings(high, low, close, p, swing_high, swing_low)
    bias = _bias_from_swings(high, low, swing_high, swing_low)
    return _ComputeOutput(
        primary=value,
        series={"value": value, "swing_high": swing_high.astype(float), "swing_low": swing_low.astype(float)},
        levels=levels,
        structure_bias=bias,
        structure_state="neutral",
        signal="swing_high" if _last_float(value) == 1.0 else "swing_low" if _last_float(value) == -1.0 else "none",
        regime=bias,
        normalized_value=float((value != 0).sum()),
        summary={"calculation": "local swing high/low"},
    )


def _zigzag(high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    threshold = float(p.swing_threshold_pct)
    pivots = pd.Series(np.nan, index=close.index, dtype=float)
    last_idx = 0
    last_price = float(close.iloc[0])
    direction = 0
    for i, price in enumerate(close.astype(float)):
        if not math.isfinite(price) or last_price == 0:
            continue
        change = (price - last_price) / abs(last_price)
        if direction >= 0 and change <= -threshold:
            pivots.iloc[last_idx] = 1.0
            direction = -1
            last_idx = i
            last_price = price
        elif direction <= 0 and change >= threshold:
            pivots.iloc[last_idx] = -1.0
            direction = 1
            last_idx = i
            last_price = price
        elif (direction >= 0 and price > last_price) or (direction <= 0 and price < last_price):
            last_idx = i
            last_price = price
    swings = pivots.fillna(0.0)
    levels = _levels_from_swings(high, low, close, p, swings == 1.0, swings == -1.0)
    return _ComputeOutput(primary=swings, series={"value": swings}, levels=levels, structure_bias=_slope_bias(close, int(p.window)), structure_state="neutral", signal="zigzag", regime="swinging", summary={"calculation": "percent-threshold zigzag"})


def _hhll(high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    swing_high, swing_low = _swing_masks(high, low, int(p.left_bars), int(p.right_bars))
    highs = high.where(swing_high).dropna()
    lows = low.where(swing_low).dropna()
    hh = len(highs) >= 2 and highs.iloc[-1] > highs.iloc[-2]
    hl = len(lows) >= 2 and lows.iloc[-1] > lows.iloc[-2]
    lh = len(highs) >= 2 and highs.iloc[-1] < highs.iloc[-2]
    ll = len(lows) >= 2 and lows.iloc[-1] < lows.iloc[-2]
    score = pd.Series(1.0 if hh and hl else -1.0 if lh and ll else 0.0, index=close.index)
    bias = "bullish" if hh and hl else "bearish" if lh and ll else "mixed"
    return _ComputeOutput(primary=score, series={"value": score, "swing_high": swing_high.astype(float), "swing_low": swing_low.astype(float)}, levels=_levels_from_swings(high, low, close, p, swing_high, swing_low), structure_bias=bias, structure_state="neutral", signal=bias, regime=bias, summary={"calculation": "latest swing sequence"})


def _structure_break(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    swing_high, swing_low = _swing_masks(high, low, int(p.left_bars), int(p.right_bars))
    levels = _levels_from_swings(high, low, close, p, swing_high, swing_low)
    last_close = _last_float(close)
    prior_highs = high.where(swing_high).dropna()
    prior_lows = low.where(swing_low).dropna()
    last_high = float(prior_highs.iloc[-1]) if not prior_highs.empty else None
    last_low = float(prior_lows.iloc[-1]) if not prior_lows.empty else None
    buffer = abs(last_close or 0.0) * float(p.breakout_buffer_pct)
    state = "neutral"
    value = 0.0
    if last_close is not None and last_high is not None and last_close > last_high + buffer:
        state, value = "breakout", 1.0
    elif last_close is not None and last_low is not None and last_close < last_low - buffer:
        state, value = "breakdown", -1.0
    bias = "bullish" if value > 0 else "bearish" if value < 0 else _bias_from_swings(high, low, swing_high, swing_low)
    if indicator == "change_of_character" and state in {"breakout", "breakdown"}:
        state = "expansion"
    series = pd.Series(value, index=close.index)
    return _ComputeOutput(primary=series, series={"value": series}, levels=levels, structure_bias=bias, structure_state=state, signal=state, regime=bias, normalized_value=abs(value) * 100.0, summary={"calculation": "close versus latest swing high/low"})


def _trendline_structure(close: pd.Series, p: StructureParams) -> _ComputeOutput:
    slope = _rolling_slope(close, int(p.window))
    fitted = _rolling_regression_endpoint(close, int(p.window))
    spread = close - fitted
    bias = _slope_bias(close, int(p.window))
    return _ComputeOutput(primary=slope, series={"value": slope, "trendline": fitted, "distance": spread}, structure_bias=bias, structure_state="neutral", signal=bias, regime=bias, normalized_value=_last_abs_percent(close, spread), summary={"calculation": "rolling regression trendline"})


def _pivot_points(high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    prev_h, prev_l, prev_c = high.shift(1), low.shift(1), close.shift(1)
    pivot = (prev_h + prev_l + prev_c) / 3.0
    r1 = 2.0 * pivot - prev_l
    s1 = 2.0 * pivot - prev_h
    r2 = pivot + (prev_h - prev_l)
    s2 = pivot - (prev_h - prev_l)
    levels = _manual_levels([(_last_float(s2), "support", 0.7), (_last_float(s1), "support", 0.8), (_last_float(pivot), "pivot", 0.6), (_last_float(r1), "resistance", 0.8), (_last_float(r2), "resistance", 0.7)])
    bias = "bullish" if (_last_float(close) or 0.0) > (_last_float(pivot) or np.inf) else "bearish" if (_last_float(close) or 0.0) < (_last_float(pivot) or -np.inf) else "range"
    return _ComputeOutput(primary=pivot, series={"value": pivot, "r1": r1, "s1": s1, "r2": r2, "s2": s2}, levels=levels, structure_bias=bias, structure_state="neutral", signal=bias, regime=bias, summary={"calculation": "classic pivot points"})


def _support_resistance(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    swing_high, swing_low = _swing_masks(high, low, int(p.left_bars), int(p.right_bars))
    levels = _levels_from_swings(high, low, close, p, swing_high, swing_low)
    zones = _zones_from_levels(levels, float(p.zone_width_pct))
    last_close = _last_float(close)
    support, resistance = _nearest_levels(close, levels)
    touches = sum(int(x.get("touch_count", 0)) for x in levels)
    if indicator == "nearest_support_resistance":
        value = pd.Series(0.0 if support is None or resistance is None else min(abs(last_close - support), abs(resistance - last_close)), index=close.index)
    elif indicator == "level_touch_count":
        value = pd.Series(float(touches), index=close.index)
    else:
        value = pd.Series(0.0 if support is None or resistance is None else float(resistance - support), index=close.index)
    return _ComputeOutput(primary=value, series={"value": value, "swing_high": swing_high.astype(float), "swing_low": swing_low.astype(float)}, levels=levels, zones=zones, structure_bias="range", structure_state="neutral", signal="levels_detected" if levels else "none", regime="range", normalized_value=float(touches), summary={"calculation": "clustered swing levels"})


def _breakout_family(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    upper = high.shift(1).rolling(int(p.window), min_periods=int(p.window)).max()
    lower = low.shift(1).rolling(int(p.window), min_periods=int(p.window)).min()
    width = (upper - lower).replace(0, np.nan)
    last_close = _last_float(close)
    buf = close.abs() * float(p.breakout_buffer_pct)
    breakout = close > upper + buf
    breakdown = close < lower - buf
    value = pd.Series(0.0, index=close.index)
    value[breakout] = 1.0
    value[breakdown] = -1.0
    state = "breakout" if bool(breakout.iloc[-1]) else "breakdown" if bool(breakdown.iloc[-1]) else "neutral"
    if indicator == "retest_detector":
        recent_break = value.shift(1).tail(int(p.retest_bars)).replace(0, np.nan).dropna()
        retest = False
        if not recent_break.empty and last_close is not None:
            level = _last_float(upper if recent_break.iloc[-1] > 0 else lower)
            retest = level is not None and abs(last_close - level) <= abs(level) * float(p.tolerance_pct)
        value = pd.Series(1.0 if retest else 0.0, index=close.index)
        state = "retest" if retest else "neutral"
    elif indicator == "false_breakout_detector":
        prev_break = value.shift(1).tail(int(p.retest_bars))
        false_up = (prev_break > 0).any() and last_close is not None and _last_float(upper) is not None and last_close < _last_float(upper)
        false_down = (prev_break < 0).any() and last_close is not None and _last_float(lower) is not None and last_close > _last_float(lower)
        value = pd.Series(1.0 if false_up else -1.0 if false_down else 0.0, index=close.index)
        state = "sweep" if false_up or false_down else "neutral"
    bias = "bullish" if _last_float(value) and _last_float(value) > 0 else "bearish" if _last_float(value) and _last_float(value) < 0 else "range"
    strength = (close - upper) / width
    return _ComputeOutput(primary=value, series={"value": value, "upper": upper, "lower": lower, "strength": strength}, levels=_manual_levels([(_last_float(lower), "support", 0.8), (_last_float(upper), "resistance", 0.8)]), zones=_zones_from_levels(_manual_levels([(_last_float(lower), "support", 0.8), (_last_float(upper), "resistance", 0.8)]), float(p.zone_width_pct)), structure_bias=bias, structure_state=state, signal=state, regime=bias, normalized_value=None if _last_float(strength) is None else abs(_last_float(strength)) * 100.0, summary={"calculation": "rolling range breakout"})


def _range_family(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    upper = high.rolling(int(p.window), min_periods=int(p.window)).max()
    lower = low.rolling(int(p.window), min_periods=int(p.window)).min()
    mid = (upper + lower) / 2.0
    width = (upper - lower).replace(0, np.nan)
    pos = (close - lower) / width
    atr_proxy = (high - low).abs().rolling(int(p.window), min_periods=int(p.window)).mean()
    compression = width / atr_proxy.replace(0, np.nan)
    if indicator == "range_position":
        primary = pos
    elif indicator == "range_breakout_strength":
        primary = pd.concat([(close - upper) / width, (lower - close) / width], axis=1).max(axis=1)
    elif indicator == "consolidation_zone":
        primary = (compression <= compression.rolling(int(p.lookback), min_periods=max(5, min(int(p.lookback), 20))).quantile(0.35)).astype(float)
    else:
        primary = width
    state = "consolidation" if indicator == "consolidation_zone" and (_last_float(primary) or 0.0) > 0 else "breakout" if indicator == "range_breakout_strength" and (_last_float(primary) or 0.0) > 0 else "neutral"
    levels = _manual_levels([(_last_float(lower), "support", 0.8), (_last_float(mid), "mid", 0.5), (_last_float(upper), "resistance", 0.8)])
    zones = _zones_from_levels(levels, float(p.zone_width_pct))
    return _ComputeOutput(primary=primary, series={"value": primary, "upper": upper, "lower": lower, "mid": mid, "position": pos}, levels=levels, zones=zones, structure_bias="range", structure_state=state, signal=state, regime="range", normalized_value=None if _last_float(pos) is None else 100.0 * _last_float(pos), summary={"calculation": "rolling range structure"})


def _bar_range_family(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    rng = (high - low).abs()
    avg = rng.rolling(int(p.window), min_periods=int(p.window)).mean()
    if indicator == "inside_bar":
        value = ((high < high.shift(1)) & (low > low.shift(1))).astype(float)
        state = "consolidation" if (_last_float(value) or 0.0) > 0 else "neutral"
    elif indicator == "outside_bar":
        value = ((high > high.shift(1)) & (low < low.shift(1))).astype(float)
        state = "expansion" if (_last_float(value) or 0.0) > 0 else "neutral"
    elif indicator == "narrow_range":
        value = (rng / avg.replace(0, np.nan))
        state = "consolidation" if (_last_float(value) or np.inf) < 0.7 else "neutral"
    else:
        value = (rng / avg.replace(0, np.nan))
        state = "expansion" if (_last_float(value) or 0.0) > 1.5 else "neutral"
    return _ComputeOutput(primary=value, series={"value": value, "range": rng, "average_range": avg}, structure_bias="range", structure_state=state, signal=state, regime=state, normalized_value=None if _last_float(value) is None else 100.0 * abs(_last_float(value)), summary={"calculation": "bar range pattern"})


def _gap_family(indicator: str, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    if indicator == "price_gap":
        gap = (open_ - close.shift(1)) / close.shift(1).abs().replace(0, np.nan)
        value = gap
    else:
        up_gap = low > high.shift(2)
        down_gap = high < low.shift(2)
        value = pd.Series(0.0, index=close.index)
        value[up_gap] = 1.0
        value[down_gap] = -1.0
    last = _last_float(value)
    state = "breakout" if last is not None and last > float(p.min_gap_pct) else "breakdown" if last is not None and last < -float(p.min_gap_pct) else "neutral"
    zones = []
    if indicator == "fair_value_gap":
        for i in range(2, len(close)):
            if low.iloc[i] > high.iloc[i - 2]:
                zones.append(_zone(high.iloc[i - 2], low.iloc[i], "fair_value_gap_up", 0.7))
            elif high.iloc[i] < low.iloc[i - 2]:
                zones.append(_zone(high.iloc[i], low.iloc[i - 2], "fair_value_gap_down", 0.7))
        zones = zones[-int(p.max_levels):]
    return _ComputeOutput(primary=value, series={"value": value}, zones=zones, structure_bias="bullish" if state == "breakout" else "bearish" if state == "breakdown" else "range", structure_state=state, signal=state, regime=state, normalized_value=None if last is None else abs(last) * 100.0, summary={"calculation": "gap detection"})


def _liquidity_family(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams) -> _ComputeOutput:
    prev_high = high.shift(1).rolling(int(p.window), min_periods=int(p.window)).max()
    prev_low = low.shift(1).rolling(int(p.window), min_periods=int(p.window)).min()
    tol_high = prev_high.abs() * float(p.tolerance_pct)
    tol_low = prev_low.abs() * float(p.tolerance_pct)
    if indicator == "equal_highs_lows":
        equal_high = (high - prev_high).abs() <= tol_high
        equal_low = (low - prev_low).abs() <= tol_low
        value = pd.Series(0.0, index=close.index)
        value[equal_high] = 1.0
        value[equal_low] = -1.0
        state = "neutral"
    else:
        sweep_high = (high > prev_high + tol_high) & (close < prev_high)
        sweep_low = (low < prev_low - tol_low) & (close > prev_low)
        value = pd.Series(0.0, index=close.index)
        value[sweep_high] = -1.0
        value[sweep_low] = 1.0
        state = "sweep" if (_last_float(value) or 0.0) != 0.0 else "neutral"
    levels = _manual_levels([(_last_float(prev_low), "support", 0.7), (_last_float(prev_high), "resistance", 0.7)])
    bias = "bullish" if (_last_float(value) or 0.0) > 0 else "bearish" if (_last_float(value) or 0.0) < 0 else "range"
    return _ComputeOutput(primary=value, series={"value": value, "prior_high": prev_high, "prior_low": prev_low}, levels=levels, structure_bias=bias, structure_state=state, signal=state, regime=bias, normalized_value=None if _last_float(value) is None else abs(_last_float(value)) * 100.0, summary={"calculation": "equal high/low and sweep detection"})


def _zone_proxy(indicator: str, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: Optional[pd.Series], p: StructureParams) -> _ComputeOutput:
    body = (close - open_).abs()
    rng = (high - low).abs().replace(0, np.nan)
    impulse = body / rng
    avg_range = rng.rolling(int(p.window), min_periods=int(p.window)).mean()
    large = rng > avg_range * 1.5
    zones: List[Dict[str, Any]] = []
    for i in range(1, len(close)):
        if not bool(large.iloc[i]):
            continue
        kind = "demand" if close.iloc[i] > open_.iloc[i] else "supply"
        lower = float(min(open_.iloc[i - 1], close.iloc[i - 1], low.iloc[i - 1]))
        upper = float(max(open_.iloc[i - 1], close.iloc[i - 1], high.iloc[i - 1]))
        zones.append(_zone(lower, upper, "order_block_proxy_" + kind if indicator == "order_block_proxy" else kind, min(1.0, float(impulse.iloc[i]) if math.isfinite(float(impulse.iloc[i])) else 0.5)))
    zones = zones[-int(p.max_levels):]
    value = pd.Series(float(len(zones)), index=close.index)
    bias = "bullish" if zones and "demand" in zones[-1]["kind"] else "bearish" if zones and "supply" in zones[-1]["kind"] else "range"
    return _ComputeOutput(primary=value, series={"value": value, "impulse": impulse}, zones=zones, structure_bias=bias, structure_state="neutral", signal="zones_detected" if zones else "none", regime=bias, normalized_value=float(len(zones)), summary={"calculation": "OHLCV impulse zone proxy"}, diagnostics={"approximation": True, "approximation_note": "OHLCV zone proxy; not footprint, order book, or verified institutional order block."})


def _profile_family(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, volume: Optional[pd.Series], p: StructureParams) -> _ComputeOutput:
    if volume is None:
        raise ValueError("profile modules require volume")
    profile = _profile(close.tail(int(p.lookback)), volume.tail(int(p.lookback)), int(p.profile_bins))
    prices = profile["prices"]
    weights = profile["weights"]
    if len(prices) == 0 or float(weights.sum()) <= 0:
        raise ValueError("profile has no usable bins")
    poc_idx = int(np.argmax(weights))
    poc = float(prices[poc_idx])
    vah, val = _value_area(prices, weights, float(p.value_area_pct))
    acceptance = 1.0 if float(close.iloc[-1]) <= vah and float(close.iloc[-1]) >= val else 0.0
    if indicator == "point_of_control":
        primary = pd.Series(poc, index=close.index)
    elif indicator == "value_area":
        primary = pd.Series(vah - val, index=close.index)
    elif indicator == "profile_acceptance":
        primary = pd.Series(acceptance, index=close.index)
    else:
        primary = pd.Series(poc, index=close.index)
    levels = _manual_levels([(val, "value_area_low", 0.8), (poc, "point_of_control", 1.0), (vah, "value_area_high", 0.8)])
    zones = [_zone(val, vah, "value_area", 1.0)]
    state = "neutral" if acceptance else "breakout" if float(close.iloc[-1]) > vah else "breakdown"
    return _ComputeOutput(primary=primary, series={"value": primary}, levels=levels, zones=zones, structure_bias="range", structure_state=state, signal=state, regime="profile", normalized_value=100.0 * acceptance, summary={"calculation": "OHLCV close-price profile approximation", "profile_bins": int(p.profile_bins)}, diagnostics={"approximation": True, "approximation_note": "Profile is binned from OHLCV close and volume, not tick-level market profile or footprint data."})


def _swing_masks(high: pd.Series, low: pd.Series, left: int, right: int) -> Tuple[pd.Series, pd.Series]:
    swing_high = pd.Series(False, index=high.index)
    swing_low = pd.Series(False, index=low.index)
    for i in range(left, len(high) - right):
        hwin = high.iloc[i - left:i + right + 1]
        lwin = low.iloc[i - left:i + right + 1]
        swing_high.iloc[i] = bool(high.iloc[i] == hwin.max() and hwin.notna().all())
        swing_low.iloc[i] = bool(low.iloc[i] == lwin.min() and lwin.notna().all())
    return swing_high, swing_low


def _levels_from_swings(high: pd.Series, low: pd.Series, close: pd.Series, p: StructureParams, swing_high: pd.Series, swing_low: pd.Series) -> List[Dict[str, Any]]:
    points: List[Tuple[float, str, int]] = []
    start = max(0, len(close) - int(p.lookback))
    for i in range(start, len(close)):
        if bool(swing_high.iloc[i]):
            points.append((float(high.iloc[i]), "resistance", i))
        if bool(swing_low.iloc[i]):
            points.append((float(low.iloc[i]), "support", i))
    levels = _cluster_levels(points, close, float(p.tolerance_pct), int(p.min_touches), int(p.max_levels))
    if levels or not points:
        return levels
    last_close = _last_float(close)
    fallback = []
    for price, kind, idx in sorted(points, key=lambda item: item[2], reverse=True)[: int(p.max_levels)]:
        fallback.append(
            {
                "price": float(price),
                "kind": kind,
                "strength": 1.0 / max(float(p.min_touches), 1.0),
                "touch_count": 1,
                "last_touch_index": int(idx),
                "_distance": 0.0 if last_close is None else abs(float(price) - last_close),
            }
        )
    fallback.sort(key=lambda x: (float(x["_distance"]), -int(x["last_touch_index"])))
    for item in fallback:
        item.pop("_distance", None)
    return fallback[: int(p.max_levels)]


def _cluster_levels(points: List[Tuple[float, str, int]], close: pd.Series, tolerance_pct: float, min_touches: int, max_levels: int) -> List[Dict[str, Any]]:
    clusters: List[Dict[str, Any]] = []
    for price, kind, idx in points:
        if not math.isfinite(price) or price == 0:
            continue
        matched = None
        for cluster in clusters:
            cluster_price = float(np.mean(cluster["prices"]))
            if abs(price - cluster_price) <= abs(cluster_price) * tolerance_pct:
                matched = cluster
                break
        if matched is None:
            clusters.append({"prices": [price], "kinds": [kind], "indices": [idx]})
        else:
            matched["prices"].append(price)
            matched["kinds"].append(kind)
            matched["indices"].append(idx)
    out = []
    last_close = _last_float(close)
    for cluster in clusters:
        touch_count = len(cluster["prices"])
        if touch_count < min_touches and len(points) >= min_touches:
            continue
        price = float(np.mean(cluster["prices"]))
        kinds = cluster["kinds"]
        kind = "resistance" if kinds.count("resistance") > kinds.count("support") else "support"
        strength = min(1.0, touch_count / max(float(min_touches), 1.0))
        distance = abs(price - last_close) if last_close is not None else 0.0
        out.append({"price": price, "kind": kind, "strength": strength, "touch_count": touch_count, "last_touch_index": int(max(cluster["indices"])), "_distance": distance})
    out.sort(key=lambda x: (-float(x["strength"]), float(x["_distance"])))
    trimmed = out[:max_levels]
    for item in trimmed:
        item.pop("_distance", None)
    return trimmed


def _manual_levels(items: List[Tuple[Optional[float], str, float]]) -> List[Dict[str, Any]]:
    levels = []
    for price, kind, strength in items:
        if price is None or not math.isfinite(float(price)):
            continue
        levels.append({"price": float(price), "kind": kind, "strength": float(strength), "touch_count": 1, "last_touch_index": -1})
    return levels


def _zones_from_levels(levels: List[Dict[str, Any]], width_pct: float) -> List[Dict[str, Any]]:
    zones = []
    for item in levels:
        price = float(item["price"])
        half = abs(price) * float(width_pct) / 2.0
        zones.append(_zone(price - half, price + half, str(item["kind"]), float(item.get("strength", 0.5))))
    return zones


def _zone(lower: float, upper: float, kind: str, strength: float) -> Dict[str, Any]:
    lo, hi = sorted([float(lower), float(upper)])
    return {"lower": lo, "upper": hi, "kind": kind, "strength": float(strength)}


def _nearest_levels(close: pd.Series, levels: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float]]:
    last = _last_float(close)
    if last is None:
        return None, None
    supports = [float(x["price"]) for x in levels if float(x["price"]) <= last]
    resistances = [float(x["price"]) for x in levels if float(x["price"]) >= last]
    return (max(supports) if supports else None, min(resistances) if resistances else None)


def _distance(price: Optional[float], level: Optional[float]) -> Optional[float]:
    if price is None or level is None or price == 0:
        return None
    return float((price - level) / abs(price))


def _bias_from_swings(high: pd.Series, low: pd.Series, swing_high: pd.Series, swing_low: pd.Series) -> str:
    highs = high.where(swing_high).dropna()
    lows = low.where(swing_low).dropna()
    if len(highs) >= 2 and len(lows) >= 2:
        if highs.iloc[-1] > highs.iloc[-2] and lows.iloc[-1] > lows.iloc[-2]:
            return "bullish"
        if highs.iloc[-1] < highs.iloc[-2] and lows.iloc[-1] < lows.iloc[-2]:
            return "bearish"
    return "range"


def _slope_bias(close: pd.Series, n: int) -> str:
    slope = _last_float(_rolling_slope(close, n))
    if slope is None:
        return "unknown"
    if slope > 0:
        return "bullish"
    if slope < 0:
        return "bearish"
    return "range"


def _rolling_slope(series: pd.Series, n: int) -> pd.Series:
    x = np.arange(int(n), dtype=float)
    x_mean = float(x.mean())
    x_var = float(((x - x_mean) ** 2).sum())

    def calc(y: np.ndarray) -> float:
        if np.isnan(y).any():
            return np.nan
        y_mean = float(y.mean())
        return float(((x - x_mean) * (y - y_mean)).sum() / x_var)

    return series.rolling(int(n), min_periods=int(n)).apply(calc, raw=True)


def _rolling_regression_endpoint(series: pd.Series, n: int) -> pd.Series:
    slope = _rolling_slope(series, n)
    mean = series.rolling(int(n), min_periods=int(n)).mean()
    x_mid = (int(n) - 1) / 2.0
    return mean + slope * x_mid


def _profile(close: pd.Series, volume: pd.Series, bins: int) -> Dict[str, np.ndarray]:
    valid = pd.DataFrame({"close": close, "volume": volume}).dropna()
    if valid.empty:
        return {"prices": np.array([]), "weights": np.array([])}
    prices = valid["close"].to_numpy(dtype=float)
    weights = valid["volume"].abs().to_numpy(dtype=float)
    if float(weights.sum()) <= 0.0 or float(np.nanmax(prices) - np.nanmin(prices)) <= 0.0:
        return {"prices": np.array([]), "weights": np.array([])}
    hist, edges = np.histogram(prices, bins=int(bins), weights=weights)
    centers = (edges[:-1] + edges[1:]) / 2.0
    return {"prices": centers, "weights": hist.astype(float)}


def _value_area(prices: np.ndarray, weights: np.ndarray, pct: float) -> Tuple[float, float]:
    total = float(weights.sum())
    target = total * float(pct) / 100.0
    order = list(np.argsort(weights)[::-1])
    selected = []
    acc = 0.0
    for idx in order:
        selected.append(int(idx))
        acc += float(weights[idx])
        if acc >= target:
            break
    vals = prices[selected]
    return float(np.nanmax(vals)), float(np.nanmin(vals))


def _last_abs_percent(price: pd.Series, value: pd.Series) -> Optional[float]:
    p = _last_float(price)
    v = _last_float(value.abs())
    if p is None or v is None or p == 0:
        return None
    return 100.0 * v / abs(p)


def _is_flat(series: pd.Series) -> bool:
    valid = series.dropna()
    return len(valid) > 1 and float(valid.max() - valid.min()) == 0.0


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series.tolist()]


def _last_float(series: pd.Series) -> Optional[float]:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return None
    value = float(valid.iloc[-1])
    return value if math.isfinite(value) else None


__all__ = [
    "StructureParams",
    "StructureReport",
    "normalize_structure_input",
    "run_structure_indicator",
]
