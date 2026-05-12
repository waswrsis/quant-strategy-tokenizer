"""
quant_strategy_tokenizer.indicators.volume_common
=================================================
Purpose: shared implementation layer for atomic volume indicator tokens.
Core idea: Normalize caller-supplied volume, price-volume, or OHLCV data,
calculate activity, accumulation/distribution, flow-pressure, and proxy order
flow measures with explicit backend handling, then return a uniform
VolumeReport. Assumes volume tokens should describe participation, confirmation,
and flow pressure without owning data sourcing or execution.
Inputs: raw user data, DataFrameSpec/ExtractorSpec, VolumeParams-compatible
configuration, indicator name, input kind, and ModuleRunContext.
Outputs: VolumeReport wrapped in ModuleResult with last values, volume
direction, volume level, flow direction, optional series, diagnostics, warnings,
and report files when requested.
Failure semantics: invalid params, missing fields, all-zero volume,
insufficient history, unsupported backend, unavailable TA-Lib, invalid
zero-denominator calculations, and calculation errors return ModuleResult.fail.
Market generalization: all calculations operate on caller-mapped numeric fields
and do not assume asset class, venue, session model, quote currency, or symbol
format.
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
class VolumeParams:
    """Generic volume-indicator options used by atomic wrapper modules.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`. Native uses pandas/numpy. Talib
      requires TA-Lib and fails explicitly if unavailable. Auto uses TA-Lib
      only for supported functions when installed.
    - `value_field`, `volume_field`: logical close/value and volume fields
      resolved through DataFrameSpec.
    - window fields: lookbacks in rows/bars. Unused fields are ignored by each
      indicator but kept for a stable interface.
    - `spike_multiplier`, `dry_up_percentile`, and percentile thresholds shape
      report labels only; modules do not place trades.
    """

    backend: str = "native"
    value_field: str = "close"
    volume_field: str = "volume"
    window: int = 20
    min_periods: Optional[int] = None
    fast_window: int = 10
    slow_window: int = 20
    signal_window: int = 9
    regime_window: int = 100
    low_percentile: float = 25.0
    high_percentile: float = 75.0
    extreme_percentile: float = 90.0
    dry_up_percentile: float = 20.0
    spike_multiplier: float = 2.5
    smoothing: str = "sma"


@dataclass
class VolumeReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    volume_direction: str = "unknown"
    volume_level: str = "unknown"
    flow_direction: str = "unknown"
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
    signal: str = "none"
    volume_direction: str = "unknown"
    volume_level: str = "unknown"
    flow_direction: str = "unknown"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_volume_input(request: Any, input_kind: str) -> ModuleResult[Any]:
    params = request.params
    value_field = str(getattr(params, "value_field", "close") or "close")
    volume_field = str(getattr(params, "volume_field", "volume") or "volume")
    if input_kind == "volume":
        primary = normalize_frame(request.data, required_fields=[volume_field], optional_fields=[], spec=request.spec, extractor=request.extractor)
        if primary.ok:
            return primary
        fallback = normalize_frame(request.data, required_fields=["value"], optional_fields=[], spec=request.spec, extractor=request.extractor)
        if fallback.ok and fallback.value is not None:
            fallback.value.used_fields[volume_field] = fallback.value.used_fields["value"]
            fallback.value.used_fields["volume"] = fallback.value.used_fields["value"]
            fallback.value.warnings.append("volume field was inferred from value column")
            return fallback
        return primary
    if input_kind == "price_volume":
        required = [value_field, volume_field]
        optional: List[str] = []
    elif input_kind == "ohlcv":
        required = ["high", "low", "close", volume_field]
        optional = ["open"]
    elif input_kind == "ohlcv_open":
        required = ["open", "high", "low", "close", volume_field]
        optional = []
    else:
        required = [value_field, volume_field]
        optional = []
    return normalize_frame(request.data, required_fields=required, optional_fields=optional, spec=request.spec, extractor=request.extractor)


def run_volume_indicator(indicator: str, request: Any, *, input_kind: str, module_name: str) -> ModuleResult[VolumeReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error

    backend_result = _resolve_backend(str(getattr(params, "backend", "native") or "native"), indicator)
    if not backend_result.ok:
        return ModuleResult.fail(backend_result.failure.kind, backend_result.failure.message, details=backend_result.failure.details)
    backend, talib_mod = backend_result.value

    norm = normalize_volume_input(request, input_kind)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")

    frame = nf.frame
    used = dict(nf.used_fields)
    volume_key = str(getattr(params, "volume_field", "volume") or "volume")
    volume_col = used.get(volume_key) or used.get("volume") or used.get("value")
    if volume_col is None:
        return ModuleResult.fail("missing_required_field", "volume indicator needs a resolved volume field")
    volume = pd.to_numeric(frame[volume_col], errors="coerce")
    if float(volume.fillna(0.0).abs().sum()) <= 0.0:
        return ModuleResult.fail("invalid_numeric", "volume field contains only zero or missing values", field=str(volume_col))

    value_key = str(getattr(params, "value_field", "close") or "close")
    close_col = used.get(value_key) or used.get("close")
    close = pd.to_numeric(frame[close_col], errors="coerce") if close_col is not None else pd.Series(np.nan, index=volume.index, dtype=float)
    open_ = pd.to_numeric(frame[used["open"]], errors="coerce") if "open" in used else close
    high = pd.to_numeric(frame[used["high"]], errors="coerce") if "high" in used else close
    low = pd.to_numeric(frame[used["low"]], errors="coerce") if "low" in used else close

    min_rows = _minimum_rows(indicator, params)
    numeric_rows = int(volume.dropna().shape[0])
    if numeric_rows < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} numeric volume rows, got {numeric_rows}")

    try:
        if backend == "talib":
            computed = _compute_talib(indicator, params, open_, high, low, close, volume, talib_mod)
        else:
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

    normalized = computed.normalized_value
    if normalized is None:
        normalized = last_percentile(primary, int(params.regime_window))
    volume_level = computed.volume_level if computed.volume_level != "unknown" else classify_volume_level(
        normalized,
        dry_up=float(params.dry_up_percentile),
        low=float(params.low_percentile),
        high=float(params.high_percentile),
        extreme=float(params.extreme_percentile),
    )
    volume_direction = computed.volume_direction
    if volume_direction == "unknown":
        volume_direction = classify_volume_direction(primary)
    flow_direction = computed.flow_direction
    if flow_direction == "unknown":
        flow_direction = classify_flow_direction(primary)
    regime = computed.regime if computed.regime != "unknown" else volume_level
    signal = computed.signal if computed.signal != "none" else _signal_from_state(volume_level, volume_direction, flow_direction)

    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = VolumeReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        volume_direction=volume_direction,
        volume_level=volume_level,
        flow_direction=flow_direction,
        signal=signal,
        regime=regime,
        normalized_value=normalized,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": int(len(volume)), "backend": backend, "input_kind": input_kind, **computed.summary},
        input_profile=nf.input_profile,
        used_fields=used,
        missing_fields=nf.missing_fields,
        warnings=nf.warnings,
        diagnostics={
            "module": module_name,
            "indicator": indicator,
            "volume_col": str(volume_col),
            "value_col": "" if close_col is None else str(close_col),
            **computed.diagnostics,
        },
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "level": volume_level, "flow": flow_direction})],
        warnings=nf.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def classify_volume_direction(series: pd.Series, *, tolerance: float = 0.01) -> str:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 2:
        return "unknown"
    prev = float(valid.iloc[-2])
    curr = float(valid.iloc[-1])
    scale = max(abs(prev), 1e-12)
    if curr > prev + scale * tolerance:
        return "increasing"
    if curr < prev - scale * tolerance:
        return "decreasing"
    return "stable"


def classify_volume_level(normalized_value: Optional[float], *, dry_up: float = 20.0, low: float = 25.0, high: float = 75.0, extreme: float = 90.0) -> str:
    if normalized_value is None or not math.isfinite(float(normalized_value)):
        return "unknown"
    value = float(normalized_value)
    if value <= float(dry_up):
        return "dry_up"
    if value <= float(low):
        return "low"
    if value <= float(high):
        return "normal"
    if value <= float(extreme):
        return "high"
    return "extreme"


def classify_flow_direction(series: pd.Series) -> str:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 2:
        return "unknown"
    diff = float(valid.iloc[-1] - valid.iloc[-2])
    if diff > 0:
        return "accumulation"
    if diff < 0:
        return "distribution"
    return "neutral"


def last_percentile(series: pd.Series, window: int) -> Optional[float]:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < max(5, min(int(window), 20)):
        return None
    tail = valid.tail(max(1, int(window)))
    last = float(tail.iloc[-1])
    return 100.0 * float((tail <= last).sum()) / float(len(tail))


def _validate_params(params: VolumeParams) -> Optional[ModuleResult[Any]]:
    backend = str(getattr(params, "backend", "native") or "native").lower()
    if backend not in {"native", "talib", "auto"}:
        return ModuleResult.fail("invalid_parameter", "backend must be native, talib, or auto", field="backend")
    for name in ("window", "fast_window", "slow_window", "signal_window", "regime_window"):
        try:
            value = int(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    for name in ("spike_multiplier", "dry_up_percentile", "low_percentile", "high_percentile", "extreme_percentile"):
        try:
            float(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)
    spike = float(getattr(params, "spike_multiplier"))
    if spike <= 0:
        return ModuleResult.fail("invalid_parameter", "spike_multiplier must be positive", field="spike_multiplier")
    dry = float(getattr(params, "dry_up_percentile"))
    low = float(getattr(params, "low_percentile"))
    high = float(getattr(params, "high_percentile"))
    extreme = float(getattr(params, "extreme_percentile"))
    if not (0.0 <= dry <= low < high < extreme <= 100.0):
        return ModuleResult.fail("invalid_parameter", "percentile thresholds must satisfy 0 <= dry_up <= low < high < extreme <= 100", field="dry_up_percentile")
    return None


def _resolve_backend(backend: str, indicator: str) -> ModuleResult[Tuple[str, Any]]:
    backend = backend.lower().strip()
    if backend == "native":
        return ModuleResult.success(("native", None))
    talib_mod = _import_talib()
    if talib_mod is None:
        if backend == "talib":
            return ModuleResult.fail("unavailable_backend", "TA-Lib backend requested but TA-Lib is not installed")
        return ModuleResult.success(("native", None))
    if indicator not in _TALIB_SUPPORTED:
        if backend == "talib":
            return ModuleResult.fail("unsupported_backend", f"TA-Lib backend is not implemented for {indicator}")
        return ModuleResult.success(("native", None))
    return ModuleResult.success(("talib", talib_mod))


def _import_talib() -> Any:
    try:
        import talib  # type: ignore

        return talib
    except Exception:
        return None


_TALIB_SUPPORTED = {"obv", "accumulation_distribution_line", "chaikin_oscillator"}


def _minimum_rows(indicator: str, p: VolumeParams) -> int:
    if indicator in {"volume_roc"}:
        return int(p.window) + 1
    if indicator in {"volume_oscillator", "chaikin_oscillator", "klinger_oscillator"}:
        return max(int(p.fast_window), int(p.slow_window)) + int(p.signal_window) + 1
    if indicator in {"volume_trend", "price_volume_divergence", "volume_confirmation"}:
        return max(int(p.window), 5) + 1
    return max(int(p.window), int(getattr(p, "min_periods", 0) or 0), 2)


def _compute_talib(indicator: str, p: VolumeParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, talib: Any) -> _ComputeOutput:
    h = high.astype(float).to_numpy()
    l = low.astype(float).to_numpy()
    c = close.astype(float).to_numpy()
    v = volume.astype(float).to_numpy()
    if indicator == "obv":
        obv = _series(talib.OBV(c, v), close.index)
        return _flow_output(indicator, obv, {"value": obv}, calculation="talib.OBV")
    if indicator == "accumulation_distribution_line":
        ad = _series(talib.AD(h, l, c, v), close.index)
        return _flow_output(indicator, ad, {"value": ad}, calculation="talib.AD")
    if indicator == "chaikin_oscillator":
        adosc = _series(talib.ADOSC(h, l, c, v, fastperiod=int(p.fast_window), slowperiod=int(p.slow_window)), close.index)
        return _flow_output(indicator, adosc, {"value": adosc}, calculation="talib.ADOSC")
    raise ValueError(f"unsupported talib indicator {indicator}")


def _compute_native(indicator: str, p: VolumeParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> _ComputeOutput:
    n = int(p.window)
    if indicator == "volume_sma":
        value = volume.rolling(n, min_periods=_min_periods(p, n)).mean()
        return _volume_output(indicator, value, {"value": value}, calculation="rolling_mean(volume)")
    if indicator == "volume_ema":
        value = volume.ewm(span=n, adjust=False, min_periods=_min_periods(p, n)).mean()
        return _volume_output(indicator, value, {"value": value}, calculation="ema(volume)")
    if indicator == "volume_roc":
        value = 100.0 * (volume / volume.shift(n).replace(0, np.nan) - 1.0)
        return _volume_output(indicator, value, {"value": value}, calculation="100*(volume/volume_n_bars_ago-1)")
    if indicator == "volume_zscore":
        mean = volume.rolling(n, min_periods=_min_periods(p, n)).mean()
        std = volume.rolling(n, min_periods=_min_periods(p, n)).std(ddof=1)
        value = (volume - mean) / std.replace(0, np.nan)
        return _volume_output(indicator, value, {"value": value, "mean": mean, "stddev": std}, calculation="rolling_zscore(volume)")
    if indicator == "relative_volume":
        base = volume.rolling(n, min_periods=_min_periods(p, n)).mean().shift(1)
        value = volume / base.replace(0, np.nan)
        signal = "spike" if (_last_float(value) or 0.0) >= float(p.spike_multiplier) else "normal"
        return _volume_output(indicator, value, {"value": value, "baseline": base}, signal=signal, calculation="volume/prior_average_volume")
    if indicator == "volume_percentile":
        pct = _rolling_percentile_series(volume, int(p.regime_window))
        level = classify_volume_level(_last_float(pct), dry_up=float(p.dry_up_percentile), low=float(p.low_percentile), high=float(p.high_percentile), extreme=float(p.extreme_percentile))
        return _ComputeOutput(primary=pct, series={"value": pct}, volume_level=level, signal=level, regime=level, normalized_value=_last_float(pct), summary={"calculation": "rolling_percentile(volume)"})
    if indicator == "volume_spike":
        base = volume.rolling(n, min_periods=_min_periods(p, n)).mean().shift(1)
        ratio = volume / base.replace(0, np.nan)
        signal = "spike" if (_last_float(ratio) or 0.0) >= float(p.spike_multiplier) else "normal"
        level = "extreme" if signal == "spike" else "normal"
        return _ComputeOutput(primary=ratio, series={"value": ratio, "baseline": base}, volume_direction="increasing" if signal == "spike" else "stable", volume_level=level, signal=signal, regime=level, normalized_value=None, summary={"calculation": "volume/prior_average_volume"})
    if indicator == "volume_dry_up":
        pct = _rolling_percentile_series(volume, int(p.regime_window))
        signal = "dry_up" if (_last_float(pct) or 100.0) <= float(p.dry_up_percentile) else "normal"
        level = "dry_up" if signal == "dry_up" else classify_volume_level(_last_float(pct), dry_up=float(p.dry_up_percentile), low=float(p.low_percentile), high=float(p.high_percentile), extreme=float(p.extreme_percentile))
        return _ComputeOutput(primary=pct, series={"value": pct}, volume_direction=classify_volume_direction(volume), volume_level=level, signal=signal, regime=level, normalized_value=_last_float(pct), summary={"calculation": "rolling_percentile(volume)"})
    if indicator == "volume_trend":
        slope = _rolling_slope(volume, n)
        return _volume_output(indicator, slope, {"value": slope}, calculation="rolling_slope(volume)")
    if indicator == "volume_oscillator":
        fast = volume.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        slow = volume.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
        value = 100.0 * (fast - slow) / slow.replace(0, np.nan)
        return _volume_output(indicator, value, {"value": value, "fast": fast, "slow": slow}, calculation="100*(fast_ema-slow_ema)/slow_ema")
    if indicator == "obv":
        signed = np.sign(close.diff()).fillna(0.0) * volume
        obv = signed.cumsum()
        return _flow_output(indicator, obv, {"value": obv, "signed_volume": signed}, calculation="cumulative(sign(close_change)*volume)")
    if indicator == "accumulation_distribution_line":
        mfv = _money_flow_volume(high, low, close, volume)
        adl = mfv.cumsum()
        return _flow_output(indicator, adl, {"value": adl, "money_flow_volume": mfv}, calculation="cumulative(CLV*volume)")
    if indicator == "chaikin_money_flow":
        mfv = _money_flow_volume(high, low, close, volume)
        cmf = mfv.rolling(n, min_periods=_min_periods(p, n)).sum() / volume.rolling(n, min_periods=_min_periods(p, n)).sum().replace(0, np.nan)
        return _flow_output(indicator, cmf, {"value": cmf, "money_flow_volume": mfv}, calculation="sum(CLV*volume)/sum(volume)")
    if indicator == "chaikin_oscillator":
        adl = _money_flow_volume(high, low, close, volume).cumsum()
        fast = adl.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        slow = adl.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
        value = fast - slow
        return _flow_output(indicator, value, {"value": value, "adl": adl, "fast": fast, "slow": slow}, calculation="EMA_fast(ADL)-EMA_slow(ADL)")
    if indicator == "volume_price_trend":
        vpt = (volume * close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)).cumsum()
        return _flow_output(indicator, vpt, {"value": vpt}, calculation="cumulative(volume*price_pct_change)")
    if indicator in {"positive_volume_index", "negative_volume_index"}:
        value = _pvi_nvi(close, volume, positive=(indicator == "positive_volume_index"))
        return _flow_output(indicator, value, {"value": value}, calculation="PVI" if indicator == "positive_volume_index" else "NVI")
    if indicator == "force_index":
        raw = close.diff() * volume
        value = raw.ewm(span=n, adjust=False, min_periods=_min_periods(p, n)).mean()
        return _flow_output(indicator, value, {"value": value, "raw_force": raw}, calculation="EMA(close_change*volume)")
    if indicator == "ease_of_movement":
        mid = (high + low) / 2.0
        raw = mid.diff() * (high - low).abs() / volume.replace(0, np.nan)
        value = raw.rolling(n, min_periods=_min_periods(p, n)).mean()
        return _flow_output(indicator, value, {"value": value, "raw_eom": raw}, calculation="mean(midpoint_change*range/volume)")
    if indicator == "intraday_intensity":
        raw = ((2.0 * close - high - low) / (high - low).replace(0, np.nan)) * volume
        value = 100.0 * raw.rolling(n, min_periods=_min_periods(p, n)).sum() / volume.rolling(n, min_periods=_min_periods(p, n)).sum().replace(0, np.nan)
        return _flow_output(indicator, value, {"value": value, "raw_intensity": raw}, calculation="100*sum(intraday_intensity_volume)/sum(volume)")
    if indicator == "money_flow_volume":
        mfv = _money_flow_volume(high, low, close, volume)
        return _flow_output(indicator, mfv, {"value": mfv}, calculation="CLV*volume")
    if indicator == "klinger_oscillator":
        typical = (high + low + close) / 3.0
        trend = np.sign(typical.diff()).replace(0, np.nan).ffill().fillna(0.0)
        vf = trend * volume * (2.0 * ((high - low).abs() / (high + low).abs().replace(0, np.nan))).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        fast = vf.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        slow = vf.ewm(span=int(p.slow_window), adjust=False, min_periods=int(p.slow_window)).mean()
        value = fast - slow
        signal_line = value.ewm(span=int(p.signal_window), adjust=False, min_periods=int(p.signal_window)).mean()
        return _flow_output(indicator, value, {"value": value, "signal_line": signal_line, "volume_force": vf}, signal=_relation_signal(value, signal_line), calculation="native Klinger-style volume force EMA spread", diagnostics={"native_approximation": True})
    if indicator == "volume_flow_indicator":
        typical = (high + low + close) / 3.0
        signed = np.sign(typical.diff()).fillna(0.0) * volume
        avg_volume = volume.rolling(n, min_periods=_min_periods(p, n)).mean()
        value = signed.rolling(n, min_periods=_min_periods(p, n)).sum() / avg_volume.replace(0, np.nan)
        return _flow_output(indicator, value, {"value": value, "signed_volume": signed}, calculation="sum(signed_volume)/average_volume")
    if indicator == "demand_index":
        pv = close.diff().fillna(0.0) * volume
        denom = pv.abs().rolling(n, min_periods=_min_periods(p, n)).mean().replace(0, np.nan)
        numerator = pv.rolling(n, min_periods=_min_periods(p, n)).mean()
        value = (numerator / denom).where(denom.notna(), 0.0)
        return _flow_output(indicator, value, {"value": value, "price_volume_pressure": pv}, calculation="mean(price_change*volume)/mean(abs(price_change*volume))")
    if indicator == "signed_volume_proxy":
        signed = _signed_volume_proxy(open_, close, volume)
        return _flow_output(indicator, signed, {"value": signed}, calculation="sign(close-open_or_close_change)*volume", diagnostics={"proxy_note": "OHLCV proxy; not bid/ask delta."})
    if indicator == "cumulative_signed_volume_proxy":
        signed = _signed_volume_proxy(open_, close, volume)
        cumulative = signed.cumsum()
        return _flow_output(indicator, cumulative, {"value": cumulative, "signed_volume_proxy": signed}, calculation="cumulative signed volume proxy", diagnostics={"proxy_note": "OHLCV proxy; not exchange order-flow CVD."})
    if indicator == "price_volume_divergence":
        price_slope = _rolling_slope(close, n)
        volume_slope = _rolling_slope(volume, n)
        value = _safe_z(price_slope, n) - _safe_z(volume_slope, n)
        signal = _divergence_signal(price_slope, volume_slope)
        return _ComputeOutput(primary=value, series={"value": value, "price_slope": price_slope, "volume_slope": volume_slope}, signal=signal, volume_direction=classify_volume_direction(volume_slope), flow_direction="neutral", summary={"calculation": "zscore(price_slope)-zscore(volume_slope)"})
    if indicator == "volume_confirmation":
        price_slope = _rolling_slope(close, n)
        volume_slope = _rolling_slope(volume, n)
        confirm = pd.Series(np.nan, index=close.index, dtype=float)
        confirm[(price_slope > 0) & (volume_slope > 0)] = 1.0
        confirm[(price_slope < 0) & (volume_slope > 0)] = -1.0
        confirm[(volume_slope <= 0)] = 0.0
        signal = "confirmed" if (_last_float(confirm) or 0.0) > 0 else "distribution_confirmed" if (_last_float(confirm) or 0.0) < 0 else "unconfirmed"
        return _ComputeOutput(primary=confirm, series={"value": confirm, "price_slope": price_slope, "volume_slope": volume_slope}, signal=signal, volume_direction=classify_volume_direction(volume_slope), flow_direction="accumulation" if signal == "confirmed" else "distribution" if signal == "distribution_confirmed" else "neutral", summary={"calculation": "price_slope and volume_slope confirmation"})
    raise ValueError(f"unsupported indicator {indicator}")


def _volume_output(indicator: str, primary: pd.Series, series: Dict[str, pd.Series], *, signal: str = "none", calculation: str = "") -> _ComputeOutput:
    return _ComputeOutput(
        primary=primary,
        series=series,
        signal=signal,
        volume_direction=classify_volume_direction(primary),
        summary={"calculation": calculation or indicator},
    )


def _flow_output(indicator: str, primary: pd.Series, series: Dict[str, pd.Series], *, signal: str = "none", calculation: str = "", diagnostics: Optional[Dict[str, Any]] = None) -> _ComputeOutput:
    return _ComputeOutput(
        primary=primary,
        series=series,
        signal=signal,
        volume_direction=classify_volume_direction(primary),
        flow_direction=classify_flow_direction(primary),
        summary={"calculation": calculation or indicator},
        diagnostics=dict(diagnostics or {}),
    )


def _money_flow_volume(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    return clv.replace([np.inf, -np.inf], np.nan).fillna(0.0) * volume


def _pvi_nvi(close: pd.Series, volume: pd.Series, *, positive: bool) -> pd.Series:
    out = pd.Series(np.nan, index=close.index, dtype=float)
    if len(close) == 0:
        return out
    out.iloc[0] = 1000.0
    pct = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    for i in range(1, len(close)):
        prev = out.iloc[i - 1]
        if pd.isna(prev):
            prev = 1000.0
        condition = volume.iloc[i] > volume.iloc[i - 1] if positive else volume.iloc[i] < volume.iloc[i - 1]
        out.iloc[i] = prev * (1.0 + pct.iloc[i]) if condition else prev
    return out


def _signed_volume_proxy(open_: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    raw_sign = np.sign((close - open_).where((close - open_).abs() > 0.0, close.diff()))
    return raw_sign.fillna(0.0) * volume


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


def _safe_z(series: pd.Series, n: int) -> pd.Series:
    mean = series.rolling(int(n), min_periods=int(n)).mean()
    std = series.rolling(int(n), min_periods=int(n)).std(ddof=1)
    z = (series - mean) / std.replace(0, np.nan)
    return z.where(std != 0, 0.0)


def _rolling_percentile_series(series: pd.Series, n: int) -> pd.Series:
    def calc(values: np.ndarray) -> float:
        vals = values[~np.isnan(values)]
        if len(vals) == 0:
            return np.nan
        last = vals[-1]
        return 100.0 * float((vals <= last).sum()) / float(len(vals))

    return series.rolling(int(n), min_periods=max(5, min(int(n), 20))).apply(calc, raw=True)


def _divergence_signal(price_slope: pd.Series, volume_slope: pd.Series) -> str:
    p = _last_float(price_slope)
    v = _last_float(volume_slope)
    if p is None or v is None:
        return "none"
    if p > 0 and v < 0:
        return "bearish_divergence"
    if p < 0 and v > 0:
        return "bearish_confirmation"
    if p > 0 and v > 0:
        return "bullish_confirmation"
    return "neutral"


def _relation_signal(a: pd.Series, b: pd.Series) -> str:
    av = _last_float(a)
    bv = _last_float(b)
    if av is None or bv is None:
        return "none"
    if av > bv:
        return "bullish"
    if av < bv:
        return "bearish"
    return "neutral"


def _signal_from_state(level: str, direction: str, flow: str) -> str:
    if level == "dry_up":
        return "dry_up"
    if level in {"high", "extreme"} and direction == "increasing":
        return "volume_expansion"
    if flow in {"accumulation", "distribution"}:
        return flow
    if direction in {"increasing", "decreasing", "stable"}:
        return direction
    return "none"


def _min_periods(p: VolumeParams, n: int) -> int:
    return int(p.min_periods if p.min_periods is not None else n)


def _series(values: Any, index: Any) -> pd.Series:
    return pd.Series(values, index=index, dtype=float)


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series.tolist()]


def _last_float(series: pd.Series) -> Optional[float]:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return None
    value = float(valid.iloc[-1])
    return value if math.isfinite(value) else None


__all__ = [
    "VolumeParams",
    "VolumeReport",
    "normalize_volume_input",
    "run_volume_indicator",
    "classify_volume_direction",
    "classify_volume_level",
    "classify_flow_direction",
    "last_percentile",
]
