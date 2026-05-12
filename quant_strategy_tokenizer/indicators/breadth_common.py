"""
quant_strategy_tokenizer.indicators.breadth_common
==================================================
Purpose: shared implementation layer for atomic market-breadth indicator
tokens.
Core idea: Normalize caller-supplied cross-sectional market data, either as a
long instrument panel, a wide close matrix, or already aggregated breadth rows,
then compute participation, advance/decline, high/low, volume breadth,
divergence, and regime diagnostics. Assumes breadth is a market-internal state
measure and not an execution decision by itself.
Inputs: raw user data, optional DataFrameSpec/ExtractorSpec, BreadthParams,
indicator name, and ModuleRunContext.
Outputs: BreadthReport wrapped in ModuleResult with latest values, breadth
direction/state, participation counts, volume breadth fields, optional series,
diagnostics, warnings, and report files when requested.
Failure semantics: missing fields, unsupported input shapes, insufficient
symbols, insufficient coverage, insufficient history, missing required volume
or weight fields, and calculation errors return ModuleResult.fail.
Market generalization: calculations operate on caller-mapped numeric columns and
do not assume asset class, venue, index provider, constituent source, broker, or
live exchange access.
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
class BreadthParams:
    """Generic breadth-indicator options used by atomic wrapper modules.

    Configuration:
    - field names identify the caller's timestamp, instrument, price, volume,
      weight, and optional benchmark/index columns.
    - window fields are rows/bars in the input time axis.
    - `min_symbols` and `min_coverage` define when cross-sectional breadth is
      trusted enough to report.
    - thresholds are numeric policy inputs for advance/decline, thrust, regime,
      and near-high/near-low diagnostics.
    """

    ts_field: str = "ts"
    symbol_field: str = "symbol"
    value_field: str = "close"
    volume_field: str = "volume"
    weight_field: str = "weight"
    index_value_field: str = "index_close"
    window: int = 20
    fast_window: int = 19
    slow_window: int = 39
    signal_window: int = 9
    ma_window: int = 50
    high_low_window: int = 252
    min_symbols: int = 10
    min_coverage: float = 0.6
    advance_threshold: float = 0.0
    breadth_thrust_threshold: float = 0.615
    high_percentile: float = 80.0
    low_percentile: float = 20.0
    near_level_pct: float = 0.05


@dataclass
class BreadthReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    breadth_direction: str = "unknown"
    breadth_state: str = "unknown"
    participation_rate: Optional[float] = None
    advance_count: Optional[int] = None
    decline_count: Optional[int] = None
    unchanged_count: Optional[int] = None
    up_volume: Optional[float] = None
    down_volume: Optional[float] = None
    sample_count: Optional[int] = None
    coverage: Optional[float] = None
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
class _BreadthData:
    kind: str
    aggregate: pd.DataFrame
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    weight: Optional[pd.DataFrame] = None
    index_close: Optional[pd.Series] = None
    used_fields: Dict[str, str] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class _ComputeOutput:
    primary: pd.Series
    series: Dict[str, pd.Series]
    breadth_direction: str = "unknown"
    breadth_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


AGG_FIELDS = {
    "advances",
    "declines",
    "unchanged",
    "up_volume",
    "down_volume",
    "new_highs",
    "new_lows",
    "sample_count",
    "index_close",
}


def normalize_breadth_input(request: Any) -> ModuleResult[_BreadthData]:
    params = request.params
    spec = request.spec or DataFrameSpec()
    raw_frame = _raw_to_frame(request.data, request.extractor)
    if not raw_frame.ok:
        return raw_frame
    frame = raw_frame.value
    if frame is None or frame.empty:
        return ModuleResult.fail("empty_input", "breadth input contains no rows")
    frame = frame.copy()
    warnings = list(raw_frame.warnings)
    cols = {str(c): c for c in frame.columns}
    input_profile = {"input_type": type(request.data).__name__, "rows": int(len(frame)), "columns": [str(c) for c in frame.columns]}

    ts_col = _find_any_col(cols, [params.ts_field, spec.ts_col])
    symbol_col = _find_col(cols, params.symbol_field)
    value_col = _find_any_col(cols, [params.value_field, spec.close_col, spec.value_col, spec.price_col])
    volume_col = _find_any_col(cols, [params.volume_field, spec.volume_col])
    weight_col = _find_col(cols, params.weight_field)
    index_col = _find_col(cols, params.index_value_field)
    used: Dict[str, str] = {}
    for key, col in (("ts", ts_col), ("symbol", symbol_col), ("value", value_col), ("volume", volume_col), ("weight", weight_col), ("index_close", index_col)):
        if col is not None:
            used[key] = str(col)

    agg_present = [name for name in AGG_FIELDS if _find_col(cols, name) is not None]
    if agg_present and symbol_col is None:
        return _normalize_aggregate(frame, params, used, input_profile, warnings)
    if symbol_col is not None:
        if value_col is None:
            return ModuleResult.fail("missing_required_field", "long-panel breadth input requires a value/close field", field=params.value_field)
        if ts_col is None:
            return ModuleResult.fail("missing_required_field", "long-panel breadth input requires a timestamp field", field=params.ts_field)
        return _normalize_panel(frame, params, ts_col, symbol_col, value_col, volume_col, weight_col, index_col, used, input_profile, warnings)
    return _normalize_wide(frame, params, ts_col, index_col, used, input_profile, warnings)


def run_breadth_indicator(indicator: str, request: Any, *, module_name: str) -> ModuleResult[BreadthReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error

    norm = normalize_breadth_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    data = norm.value
    if data is None:
        return ModuleResult.fail("internal_error", "breadth normalization returned no data")

    need_panel = indicator in {
        "percent_above_ma",
        "percent_above_ema",
        "percent_above_threshold",
        "percent_near_high",
        "percent_near_low",
        "cross_sectional_dispersion",
        "cross_sectional_correlation_proxy",
        "equal_weighted_return",
        "cap_weighted_breadth",
    }
    if need_panel and data.close is None:
        return ModuleResult.fail("missing_required_field", f"{indicator} requires panel or wide close data")
    if indicator in {"up_down_volume_ratio", "up_down_volume_line", "volume_advance_decline_percent", "arms_index", "trin", "volume_breadth_thrust"}:
        if not _has_volume_breadth(data.aggregate):
            return ModuleResult.fail("missing_required_field", f"{indicator} requires up_volume/down_volume or panel volume data", field=params.volume_field)
    if indicator == "cap_weighted_breadth" and data.weight is None:
        return ModuleResult.fail("missing_required_field", "cap_weighted_breadth requires a weight field", field=params.weight_field)
    if indicator in {"index_breadth_divergence", "breadth_confirmation"} and data.index_close is None:
        return ModuleResult.fail("missing_required_field", f"{indicator} requires index_close or equivalent benchmark field", field=params.index_value_field)

    agg = data.aggregate
    last_sample = _last_float(agg["sample_count"])
    last_coverage = _last_float(agg["coverage"])
    if last_sample is None or last_sample < int(params.min_symbols):
        return ModuleResult.fail("insufficient_sample", f"need at least {int(params.min_symbols)} symbols, got {0 if last_sample is None else int(last_sample)}")
    if last_coverage is None or last_coverage < float(params.min_coverage):
        return ModuleResult.fail("insufficient_coverage", f"need coverage >= {float(params.min_coverage):.3f}, got {0.0 if last_coverage is None else float(last_coverage):.3f}")
    directional_events = float((agg["advances"].fillna(0.0) + agg["declines"].fillna(0.0)).sum())
    if directional_events <= 0.0:
        return ModuleResult.fail("insufficient_data", "breadth input has no directional advance or decline events")

    min_rows = _minimum_rows(indicator, params)
    if len(agg) < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} rows, got {len(agg)}")

    try:
        computed = _compute_native(indicator, params, data)
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
    last_row = agg.iloc[-1]
    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = BreadthReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        breadth_direction=computed.breadth_direction,
        breadth_state=computed.breadth_state,
        participation_rate=_safe_float(last_row.get("participation_rate")),
        advance_count=_safe_int(last_row.get("advances")),
        decline_count=_safe_int(last_row.get("declines")),
        unchanged_count=_safe_int(last_row.get("unchanged")),
        up_volume=_safe_float(last_row.get("up_volume")),
        down_volume=_safe_float(last_row.get("down_volume")),
        sample_count=_safe_int(last_row.get("sample_count")),
        coverage=_safe_float(last_row.get("coverage")),
        signal=computed.signal,
        regime=computed.regime,
        normalized_value=computed.normalized_value,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": int(len(agg)), "input_kind": data.kind, **computed.summary},
        input_profile=data.input_profile,
        used_fields=data.used_fields,
        warnings=data.warnings,
        diagnostics={"module": module_name, "indicator": indicator, **computed.diagnostics},
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "state": report.breadth_state, "direction": report.breadth_direction})],
        warnings=data.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _normalize_aggregate(frame: pd.DataFrame, p: BreadthParams, used: Dict[str, str], input_profile: Dict[str, Any], warnings: List[str]) -> ModuleResult[_BreadthData]:
    cols = {str(c): c for c in frame.columns}
    ts_col = _find_col(cols, p.ts_field)
    out = pd.DataFrame(index=_make_index(frame, ts_col))
    for name in AGG_FIELDS:
        col = _find_col(cols, name)
        if col is not None:
            out[name] = pd.to_numeric(frame[col], errors="coerce").to_numpy()
            used[name] = str(col)
    for name in ("advances", "declines", "unchanged"):
        if name not in out:
            out[name] = 0.0
    if "sample_count" not in out:
        out["sample_count"] = out["advances"].fillna(0.0) + out["declines"].fillna(0.0) + out["unchanged"].fillna(0.0)
    for name in ("up_volume", "down_volume", "new_highs", "new_lows"):
        if name not in out:
            out[name] = np.nan
    out["coverage"] = 1.0
    denom = out["sample_count"].replace(0, np.nan)
    out["participation_rate"] = (out["advances"] + out["declines"]) / denom
    index_close = out["index_close"] if "index_close" in out else None
    if "index_close" not in out:
        out["index_close"] = np.nan
    out = out.sort_index()
    return ModuleResult.success(_BreadthData(kind="aggregate", aggregate=out, index_close=index_close, used_fields=used, input_profile=input_profile, warnings=warnings))


def _normalize_panel(
    frame: pd.DataFrame,
    p: BreadthParams,
    ts_col: Any,
    symbol_col: Any,
    value_col: Any,
    volume_col: Optional[Any],
    weight_col: Optional[Any],
    index_col: Optional[Any],
    used: Dict[str, str],
    input_profile: Dict[str, Any],
    warnings: List[str],
) -> ModuleResult[_BreadthData]:
    work = frame[[ts_col, symbol_col, value_col] + ([volume_col] if volume_col is not None else []) + ([weight_col] if weight_col is not None else []) + ([index_col] if index_col is not None else [])].copy()
    work[ts_col] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    if work[ts_col].isna().any():
        return ModuleResult.fail("invalid_timestamp", "timestamp field contains invalid values", field=str(ts_col))
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    if work[value_col].isna().all():
        return ModuleResult.fail("invalid_numeric", "value field contains no numeric values", field=str(value_col))
    close = work.pivot_table(index=ts_col, columns=symbol_col, values=value_col, aggfunc="last").sort_index()
    volume = None
    if volume_col is not None:
        work[volume_col] = pd.to_numeric(work[volume_col], errors="coerce")
        volume = work.pivot_table(index=ts_col, columns=symbol_col, values=volume_col, aggfunc="last").reindex(close.index)
    weight = None
    if weight_col is not None:
        work[weight_col] = pd.to_numeric(work[weight_col], errors="coerce")
        weight = work.pivot_table(index=ts_col, columns=symbol_col, values=weight_col, aggfunc="last").reindex(close.index)
    index_close = None
    if index_col is not None:
        work[index_col] = pd.to_numeric(work[index_col], errors="coerce")
        index_close = work.groupby(ts_col)[index_col].first().reindex(close.index)
    agg = _aggregate_from_close(close, volume, p)
    if index_close is not None:
        agg["index_close"] = index_close
    return ModuleResult.success(_BreadthData(kind="panel", aggregate=agg, close=close, volume=volume, weight=weight, index_close=index_close, used_fields=used, input_profile=input_profile, warnings=warnings))


def _normalize_wide(frame: pd.DataFrame, p: BreadthParams, ts_col: Optional[Any], index_col: Optional[Any], used: Dict[str, str], input_profile: Dict[str, Any], warnings: List[str]) -> ModuleResult[_BreadthData]:
    work = frame.copy()
    index_close = None
    if ts_col is not None:
        work[ts_col] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
        if work[ts_col].isna().any():
            return ModuleResult.fail("invalid_timestamp", "timestamp field contains invalid values", field=str(ts_col))
        work = work.set_index(ts_col)
        used["ts"] = str(ts_col)
    if index_col is not None and index_col in work.columns:
        index_close = pd.to_numeric(work[index_col], errors="coerce")
        work = work.drop(columns=[index_col])
        used["index_close"] = str(index_col)
    numeric = work.apply(pd.to_numeric, errors="coerce")
    numeric = numeric.dropna(axis=1, how="all")
    if numeric.shape[1] < 2:
        return ModuleResult.fail("missing_required_field", "wide breadth input requires at least two numeric instrument columns")
    close = numeric.sort_index()
    agg = _aggregate_from_close(close, None, p)
    if index_close is not None:
        agg["index_close"] = index_close.reindex(close.index)
    used["wide_value_columns"] = ",".join(str(c) for c in close.columns)
    return ModuleResult.success(_BreadthData(kind="wide", aggregate=agg, close=close, index_close=index_close, used_fields=used, input_profile=input_profile, warnings=warnings))


def _aggregate_from_close(close: pd.DataFrame, volume: Optional[pd.DataFrame], p: BreadthParams) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    valid = returns.notna()
    adv = returns > float(p.advance_threshold)
    dec = returns < -float(p.advance_threshold)
    sample = valid.sum(axis=1).astype(float)
    total = max(int(close.shape[1]), 1)
    agg = pd.DataFrame(index=close.index)
    agg["advances"] = adv.sum(axis=1).astype(float)
    agg["declines"] = dec.sum(axis=1).astype(float)
    agg["unchanged"] = (valid & ~adv & ~dec).sum(axis=1).astype(float)
    agg["sample_count"] = sample
    agg["coverage"] = sample / float(total)
    agg["participation_rate"] = (agg["advances"] + agg["declines"]) / sample.replace(0, np.nan)
    if volume is not None:
        aligned_volume = volume.reindex_like(close)
        agg["up_volume"] = aligned_volume.where(adv).sum(axis=1, min_count=1)
        agg["down_volume"] = aligned_volume.where(dec).sum(axis=1, min_count=1)
    else:
        agg["up_volume"] = np.nan
        agg["down_volume"] = np.nan
    roll_high = close.rolling(int(p.high_low_window), min_periods=min(int(p.high_low_window), max(2, int(p.window)))).max()
    roll_low = close.rolling(int(p.high_low_window), min_periods=min(int(p.high_low_window), max(2, int(p.window)))).min()
    agg["new_highs"] = (close >= roll_high).sum(axis=1).astype(float)
    agg["new_lows"] = (close <= roll_low).sum(axis=1).astype(float)
    agg["index_close"] = np.nan
    return agg


def _compute_native(indicator: str, p: BreadthParams, data: _BreadthData) -> _ComputeOutput:
    agg = data.aggregate
    sample = agg["sample_count"].replace(0, np.nan)
    advances = agg["advances"]
    declines = agg["declines"]
    net = advances - declines
    ad_percent = net / sample * 100.0
    adv_ratio = _bounded_ratio(advances, declines)
    adv_share = advances / (advances + declines).replace(0, np.nan)
    new_highs = agg["new_highs"]
    new_lows = agg["new_lows"]
    up_volume = agg["up_volume"]
    down_volume = agg["down_volume"]

    if indicator == "advance_decline_line":
        primary = net.fillna(0.0).cumsum()
    elif indicator == "advance_decline_ratio":
        primary = adv_ratio
    elif indicator == "advance_decline_percent":
        primary = ad_percent
    elif indicator == "net_advances":
        primary = net
    elif indicator == "absolute_breadth_index":
        primary = net.abs()
    elif indicator == "breadth_thrust":
        primary = adv_share.rolling(int(p.window), min_periods=int(p.window)).mean()
    elif indicator == "mcclellan_oscillator":
        primary = net.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean() - net.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
    elif indicator == "mcclellan_summation_index":
        osc = net.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean() - net.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
        primary = osc.fillna(0.0).cumsum()
    elif indicator == "mcclellan_ratio_adjusted_oscillator":
        ratio = net / sample * 1000.0
        primary = ratio.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean() - ratio.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
    elif indicator == "new_highs":
        primary = new_highs
    elif indicator == "new_lows":
        primary = new_lows
    elif indicator == "net_new_highs":
        primary = new_highs - new_lows
    elif indicator == "new_high_new_low_ratio":
        primary = _bounded_ratio(new_highs, new_lows)
    elif indicator == "high_low_index":
        primary = new_highs / (new_highs + new_lows).replace(0, np.nan) * 100.0
    elif indicator == "cumulative_new_highs_new_lows":
        primary = (new_highs - new_lows).fillna(0.0).cumsum()
    elif indicator == "percent_positive_return":
        primary = advances / sample * 100.0
    elif indicator == "percent_above_ma":
        primary = _percent_above_ma(data.close, int(p.ma_window), ema=False)
    elif indicator == "percent_above_ema":
        primary = _percent_above_ma(data.close, int(p.ma_window), ema=True)
    elif indicator == "percent_above_threshold":
        returns = data.close.pct_change(fill_method=None)
        primary = (returns > float(p.advance_threshold)).sum(axis=1) / returns.notna().sum(axis=1).replace(0, np.nan) * 100.0
    elif indicator == "percent_near_high":
        primary = _percent_near_extreme(data.close, int(p.high_low_window), float(p.near_level_pct), high=True)
    elif indicator == "percent_near_low":
        primary = _percent_near_extreme(data.close, int(p.high_low_window), float(p.near_level_pct), high=False)
    elif indicator == "up_down_volume_ratio":
        primary = _bounded_ratio(up_volume, down_volume)
    elif indicator == "up_down_volume_line":
        primary = (up_volume - down_volume).fillna(0.0).cumsum()
    elif indicator == "volume_advance_decline_percent":
        primary = (up_volume - down_volume) / (up_volume + down_volume).replace(0, np.nan) * 100.0
    elif indicator in {"arms_index", "trin"}:
        primary = _bounded_ratio(advances, declines) / _bounded_ratio(up_volume, down_volume).replace(0, np.nan)
    elif indicator == "volume_breadth_thrust":
        primary = (up_volume / (up_volume + down_volume).replace(0, np.nan)).rolling(int(p.window), min_periods=int(p.window)).mean()
    elif indicator == "cross_sectional_dispersion":
        primary = data.close.pct_change(fill_method=None).std(axis=1) * 100.0
    elif indicator == "cross_sectional_correlation_proxy":
        primary = _rolling_average_correlation(data.close.pct_change(fill_method=None), int(p.window))
    elif indicator == "equal_weighted_return":
        primary = data.close.pct_change(fill_method=None).mean(axis=1) * 100.0
    elif indicator == "cap_weighted_breadth":
        primary = _cap_weighted_breadth(data.close.pct_change(fill_method=None), data.weight, float(p.advance_threshold))
    elif indicator == "breadth_momentum":
        primary = ad_percent - ad_percent.rolling(int(p.window), min_periods=int(p.window)).mean()
    elif indicator == "breadth_regime":
        primary = advances / sample * 100.0
    elif indicator == "index_breadth_divergence":
        primary = _index_breadth_divergence(data.index_close, ad_percent, int(p.window))
    elif indicator == "breadth_confirmation":
        primary = _breadth_confirmation(data.index_close, ad_percent, int(p.window))
    elif indicator == "breadth_freeze_pressure":
        primary = pd.concat([advances / sample, declines / sample], axis=1).max(axis=1) * 100.0
    else:
        raise ValueError(f"unsupported indicator {indicator}")

    last = _last_float(primary)
    direction = _direction_from_value(indicator, last)
    state, signal, regime = _state_signal_regime(indicator, last, p)
    normalized = _normalized_value(indicator, primary, p)
    series = {
        "value": primary,
        "advances": advances,
        "declines": declines,
        "net_advances": net,
        "advance_decline_percent": ad_percent,
        "participation_rate": agg["participation_rate"],
        "sample_count": sample,
        "coverage": agg["coverage"],
    }
    if _has_volume_breadth(agg):
        series["up_volume"] = up_volume
        series["down_volume"] = down_volume
    if data.index_close is not None:
        series["index_close"] = data.index_close
    return _ComputeOutput(
        primary=primary,
        series=series,
        breadth_direction=direction,
        breadth_state=state,
        signal=signal,
        regime=regime,
        normalized_value=normalized,
        summary={"calculation": indicator, "input_kind": data.kind},
        diagnostics={"min_symbols": int(p.min_symbols), "min_coverage": float(p.min_coverage)},
    )


def _validate_params(p: BreadthParams) -> Optional[ModuleResult[Any]]:
    int_fields = ("window", "fast_window", "slow_window", "signal_window", "ma_window", "high_low_window", "min_symbols")
    for name in int_fields:
        try:
            value = int(getattr(p, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if int(p.fast_window) >= int(p.slow_window):
        return ModuleResult.fail("invalid_parameter", "fast_window must be smaller than slow_window", field="fast_window")
    for name in ("min_coverage", "breadth_thrust_threshold", "near_level_pct"):
        value = _safe_float(getattr(p, name))
        if value is None or value < 0.0 or value > 1.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be between 0 and 1", field=name)
    for name in ("high_percentile", "low_percentile"):
        value = _safe_float(getattr(p, name))
        if value is None or value < 0.0 or value > 100.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be between 0 and 100", field=name)
    if float(p.low_percentile) >= float(p.high_percentile):
        return ModuleResult.fail("invalid_parameter", "low_percentile must be below high_percentile", field="low_percentile")
    if _safe_float(p.advance_threshold) is None:
        return ModuleResult.fail("invalid_parameter", "advance_threshold must be numeric", field="advance_threshold")
    return None


def _minimum_rows(indicator: str, p: BreadthParams) -> int:
    if indicator in {"mcclellan_oscillator", "mcclellan_summation_index", "mcclellan_ratio_adjusted_oscillator"}:
        return int(p.slow_window)
    if indicator in {"percent_above_ma", "percent_above_ema"}:
        return int(p.ma_window)
    if indicator in {"new_highs", "new_lows", "net_new_highs", "new_high_new_low_ratio", "high_low_index", "cumulative_new_highs_new_lows", "percent_near_high", "percent_near_low"}:
        return min(int(p.high_low_window), max(int(p.window), 20))
    if indicator in {"cross_sectional_correlation_proxy", "breadth_momentum", "index_breadth_divergence", "breadth_confirmation", "breadth_thrust", "volume_breadth_thrust"}:
        return int(p.window)
    return 2


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
        return ModuleResult.fail("invalid_input", "could not convert breadth input to DataFrame", details={"error": str(exc)})
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


def _make_index(frame: pd.DataFrame, ts_col: Optional[Any]) -> pd.Index:
    if ts_col is None:
        return pd.RangeIndex(len(frame))
    converted = pd.to_datetime(frame[ts_col], utc=True, errors="coerce")
    return pd.Index(converted)


def _has_volume_breadth(agg: pd.DataFrame) -> bool:
    if "up_volume" not in agg or "down_volume" not in agg:
        return False
    total = agg["up_volume"].fillna(0.0).abs() + agg["down_volume"].fillna(0.0).abs()
    return bool(float(total.sum()) > 0.0)


def _percent_above_ma(close: pd.DataFrame, n: int, *, ema: bool) -> pd.Series:
    avg = close.ewm(span=n, adjust=False, min_periods=n).mean() if ema else close.rolling(n, min_periods=n).mean()
    valid = close.notna() & avg.notna()
    return (close > avg).sum(axis=1) / valid.sum(axis=1).replace(0, np.nan) * 100.0


def _percent_near_extreme(close: pd.DataFrame, n: int, pct: float, *, high: bool) -> pd.Series:
    min_periods = min(n, max(2, n // 4))
    ref = close.rolling(n, min_periods=min_periods).max() if high else close.rolling(n, min_periods=min_periods).min()
    valid = close.notna() & ref.notna()
    if high:
        near = close >= ref * (1.0 - pct)
    else:
        near = close <= ref * (1.0 + pct)
    return near.sum(axis=1) / valid.sum(axis=1).replace(0, np.nan) * 100.0


def _rolling_average_correlation(returns: pd.DataFrame, n: int) -> pd.Series:
    vals: List[float] = []
    idx = returns.index
    for i in range(len(returns)):
        if i + 1 < n:
            vals.append(np.nan)
            continue
        window = returns.iloc[i + 1 - n:i + 1].dropna(axis=1, how="all")
        if window.shape[1] < 2:
            vals.append(np.nan)
            continue
        corr = window.corr().to_numpy(dtype=float)
        tri = corr[np.triu_indices_from(corr, k=1)]
        tri = tri[np.isfinite(tri)]
        vals.append(float(np.mean(tri)) if len(tri) else np.nan)
    return pd.Series(vals, index=idx, dtype=float)


def _cap_weighted_breadth(returns: pd.DataFrame, weights: pd.DataFrame, threshold: float) -> pd.Series:
    aligned_weights = weights.reindex_like(returns)
    valid = returns.notna() & aligned_weights.notna()
    total = aligned_weights.where(valid).abs().sum(axis=1).replace(0, np.nan)
    score = aligned_weights.where(returns > threshold, 0.0).sum(axis=1) - aligned_weights.where(returns < -threshold, 0.0).sum(axis=1)
    return score / total * 100.0


def _bounded_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    ratio = numerator / denominator.replace(0, np.nan)
    only_numerator = denominator.fillna(0.0).abs() <= 0.0
    ratio[only_numerator & (numerator.fillna(0.0).abs() > 0.0)] = numerator[only_numerator & (numerator.fillna(0.0).abs() > 0.0)]
    ratio[only_numerator & (numerator.fillna(0.0).abs() <= 0.0)] = 0.0
    return ratio


def _index_breadth_divergence(index_close: pd.Series, breadth: pd.Series, n: int) -> pd.Series:
    index_mom = index_close.pct_change(n)
    breadth_mom = breadth - breadth.shift(n)
    out = pd.Series(0.0, index=breadth.index)
    out[(index_mom > 0) & (breadth_mom < 0)] = -1.0
    out[(index_mom < 0) & (breadth_mom > 0)] = 1.0
    return out


def _breadth_confirmation(index_close: pd.Series, breadth: pd.Series, n: int) -> pd.Series:
    index_mom = index_close.pct_change(n)
    breadth_mom = breadth - breadth.shift(n)
    out = pd.Series(0.0, index=breadth.index)
    out[(index_mom > 0) & (breadth_mom > 0)] = 1.0
    out[(index_mom < 0) & (breadth_mom < 0)] = -1.0
    return out


def _direction_from_value(indicator: str, value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if indicator in {"arms_index", "trin"}:
        if value < 0.8:
            return "bullish"
        if value > 1.2:
            return "bearish"
        return "neutral"
    if indicator in {"new_lows", "percent_near_low"}:
        return "bearish" if value > 0 else "neutral"
    if indicator in {"breadth_regime", "percent_positive_return", "percent_above_ma", "percent_above_ema", "percent_above_threshold", "percent_near_high", "high_low_index"}:
        if value >= 60.0:
            return "bullish"
        if value <= 40.0:
            return "bearish"
        return "neutral"
    if value > 0:
        return "bullish"
    if value < 0:
        return "bearish"
    return "neutral"


def _state_signal_regime(indicator: str, value: Optional[float], p: BreadthParams) -> Tuple[str, str, str]:
    if value is None:
        return "unknown", "none", "unknown"
    if indicator in {"breadth_thrust", "volume_breadth_thrust"}:
        state = "thrust" if value >= float(p.breadth_thrust_threshold) else "neutral"
        return state, state, "risk_on" if state == "thrust" else "neutral"
    if indicator in {"index_breadth_divergence"}:
        state = "bearish_divergence" if value < 0 else "bullish_divergence" if value > 0 else "neutral"
        return state, state, "divergence" if value else "neutral"
    if indicator in {"breadth_confirmation"}:
        state = "confirmed_up" if value > 0 else "confirmed_down" if value < 0 else "neutral"
        return state, state, "confirmed" if value else "neutral"
    if indicator == "breadth_freeze_pressure":
        state = "freeze_pressure" if value >= 80.0 else "broad_pressure" if value >= 65.0 else "neutral"
        return state, state, "risk_off" if value >= 80.0 else "watch"
    if indicator in {"arms_index", "trin"}:
        state = "oversold_pressure" if value > 1.2 else "buying_pressure" if value < 0.8 else "neutral"
        return state, state, state
    if indicator == "breadth_regime":
        state = "broad_up" if value >= float(p.high_percentile) else "broad_down" if value <= float(p.low_percentile) else "mixed"
        return state, state, state
    direction = _direction_from_value(indicator, value)
    state = "broad_up" if direction == "bullish" else "broad_down" if direction == "bearish" else "neutral"
    return state, state, state


def _normalized_value(indicator: str, series: pd.Series, p: BreadthParams) -> Optional[float]:
    last = _last_float(series)
    if last is None:
        return None
    if indicator in {"breadth_thrust", "volume_breadth_thrust"}:
        return float(last * 100.0)
    if indicator in {"breadth_regime", "percent_positive_return", "percent_above_ma", "percent_above_ema", "percent_above_threshold", "percent_near_high", "percent_near_low", "high_low_index", "breadth_freeze_pressure"}:
        return float(last)
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < int(p.window):
        return None
    rank = (valid <= last).sum() / len(valid) * 100.0
    return float(rank)


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series.tolist()]


def _last_float(series: pd.Series) -> Optional[float]:
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


def _safe_int(value: Any) -> Optional[int]:
    val = _safe_float(value)
    return None if val is None else int(round(val))


__all__ = ["BreadthParams", "BreadthReport", "normalize_breadth_input", "run_breadth_indicator"]
