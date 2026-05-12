"""
quant_strategy_tokenizer.indicators.trend_common
================================================
Module purpose: shared implementation layer for atomic trend indicator tokens.
Core idea: Resolve inputs, validate parameters, choose native or optional TA-Lib backend, run the selected numerical routine, and build a uniform TrendReport. Assumes public indicator modules should stay small wrappers while calculation semantics, backend policy, explicit failure states, and output shaping remain consistent.
Inputs: raw user data, DataFrameSpec/ExtractorSpec, TrendParams-compatible configuration, indicator name, input kind, and ModuleRunContext.
Outputs: TrendReport wrapped in ModuleResult with last values, direction, strength, optional series, diagnostics, warnings, and report files when requested.
Failure semantics: invalid params, missing fields, insufficient history, unsupported backend, unavailable TA-Lib, and calculation errors return ModuleResult.fail.
Market generalization: all calculations operate on caller-supplied numeric fields and do not assume asset class, venue, session model, or symbol format.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class TrendParams:
    """Generic trend-indicator options used by atomic wrapper modules.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`. Native uses pandas/numpy. Talib
      requires TA-Lib and fails explicitly if unavailable. Auto uses TA-Lib
      only for supported functions when installed.
    - `value_field`, `volume_field`: logical fields resolved through
      DataFrameSpec. Most trend modules use close as the value field.
    - window fields: per-indicator lookbacks in rows/bars. Unused fields are
      ignored by each indicator but kept for a stable interface.
    - algorithm fields: multipliers, shifts, acceleration factors, and Ehlers
      limits used by specific trend modules.
    """

    backend: str = "native"
    value_field: str = "close"
    volume_field: str = "volume"
    window: int = 20
    min_periods: Optional[int] = None
    fast_window: int = 12
    slow_window: int = 26
    signal_window: int = 9
    short_window: int = 9
    medium_window: int = 21
    long_window: int = 50
    atr_window: int = 14
    channel_window: int = 20
    smoothing: str = "ema"
    adjust: bool = False
    multiplier: float = 3.0
    acceleration: float = 0.02
    maximum: float = 0.20
    vfactor: float = 0.70
    mcginley_k: float = 0.60
    forecast_periods: int = 1
    tenkan_window: int = 9
    kijun_window: int = 26
    senkou_b_window: int = 52
    displacement: int = 26
    jaw_window: int = 13
    teeth_window: int = 8
    lips_window: int = 5
    jaw_shift: int = 8
    teeth_shift: int = 5
    lips_shift: int = 3
    periods: Optional[List[int]] = None
    short_periods: Optional[List[int]] = None
    long_periods: Optional[List[int]] = None
    mama_fast_limit: float = 0.50
    mama_slow_limit: float = 0.05
    cycle_window: int = 32


@dataclass
class TrendReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    trend_direction: str = "unknown"
    trend_strength: Optional[float] = None
    signal: str = "none"
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
    trend_direction: str = "unknown"
    trend_strength: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_trend_input(request: Any, input_kind: str) -> ModuleResult[Any]:
    params = request.params
    if input_kind == "price":
        required = [str(getattr(params, "value_field", "close") or "close")]
        optional: List[str] = []
    elif input_kind == "price_volume":
        required = [
            str(getattr(params, "value_field", "close") or "close"),
            str(getattr(params, "volume_field", "volume") or "volume"),
        ]
        optional = []
    elif input_kind == "ohlcv":
        required = ["high", "low", "close", str(getattr(params, "volume_field", "volume") or "volume")]
        optional = []
    else:
        required = ["high", "low", "close"]
        optional = []
    return normalize_frame(request.data, required_fields=required, optional_fields=optional, spec=request.spec, extractor=request.extractor)


def run_trend_indicator(indicator: str, request: Any, *, input_kind: str, module_name: str) -> ModuleResult[TrendReport]:
    params = request.params
    param_error = _validate_params(indicator, params)
    if param_error is not None:
        return param_error

    backend_result = _resolve_backend(str(getattr(params, "backend", "native") or "native"), indicator)
    if not backend_result.ok:
        return ModuleResult.fail(backend_result.failure.kind, backend_result.failure.message, details=backend_result.failure.details)
    backend, talib_mod = backend_result.value

    norm = normalize_trend_input(request, input_kind)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")

    frame = nf.frame
    used = dict(nf.used_fields)
    close_col = used.get(str(getattr(params, "value_field", "close") or "close")) or used.get("close")
    if close_col is None:
        return ModuleResult.fail("missing_required_field", "trend indicator needs a resolved price field")
    close = pd.to_numeric(frame[close_col], errors="coerce")
    high = pd.to_numeric(frame[used["high"]], errors="coerce") if "high" in used else close
    low = pd.to_numeric(frame[used["low"]], errors="coerce") if "low" in used else close
    volume_col = used.get(str(getattr(params, "volume_field", "volume") or "volume"))
    volume = pd.to_numeric(frame[volume_col], errors="coerce") if volume_col is not None else None

    min_rows = _minimum_rows(indicator, params)
    if int(close.dropna().shape[0]) < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} numeric rows, got {int(close.dropna().shape[0])}")

    try:
        if backend == "talib":
            computed = _compute_talib(indicator, params, close, high, low, volume, talib_mod)
        else:
            computed = _compute_native(indicator, params, close, high, low, volume)
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

    direction = computed.trend_direction
    if direction == "unknown":
        direction = _direction_from_price(close, primary)
    strength = computed.trend_strength
    if strength is None:
        strength = _default_strength(close, primary)

    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = TrendReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        trend_direction=direction,
        trend_strength=strength,
        signal=computed.signal,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={
            "rows": int(len(close)),
            "backend": backend,
            "input_kind": input_kind,
            **computed.summary,
        },
        input_profile=nf.input_profile,
        used_fields=used,
        missing_fields=nf.missing_fields,
        warnings=nf.warnings,
        diagnostics={
            "module": module_name,
            "indicator": indicator,
            "value_col": str(close_col),
            **computed.diagnostics,
        } if detail_at_least(detail, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{module_name}.calculated", fields={"indicator": indicator, "last_value": last, "backend": backend})],
        warnings=nf.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _validate_params(indicator: str, params: TrendParams) -> Optional[ModuleResult[TrendReport]]:
    def int_value(name: str) -> Tuple[Optional[int], Optional[ModuleResult[TrendReport]]]:
        try:
            return int(getattr(params, name)), None
        except Exception:
            return None, ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)

    def float_value(name: str) -> Tuple[Optional[float], Optional[ModuleResult[TrendReport]]]:
        try:
            return float(getattr(params, name)), None
        except Exception:
            return None, ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)

    numeric_windows = [
        "window", "fast_window", "slow_window", "signal_window", "short_window", "medium_window", "long_window",
        "atr_window", "channel_window", "tenkan_window", "kijun_window", "senkou_b_window", "displacement",
        "jaw_window", "teeth_window", "lips_window", "jaw_shift", "teeth_shift", "lips_shift", "cycle_window",
    ]
    for name in numeric_windows:
        value, err = int_value(name)
        if err is not None:
            return err
        if value is None or value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if params.min_periods is not None:
        try:
            min_periods = int(params.min_periods)
        except Exception:
            return ModuleResult.fail("invalid_parameter", "min_periods must be an integer", field="min_periods")
        if min_periods <= 0:
            return ModuleResult.fail("invalid_parameter", "min_periods must be positive when provided", field="min_periods")
    for name in ("periods", "short_periods", "long_periods"):
        values = getattr(params, name, None)
        if values is not None:
            try:
                if any(int(v) <= 0 for v in values):
                    return ModuleResult.fail("invalid_parameter", f"{name} values must be positive", field=name)
            except Exception:
                return ModuleResult.fail("invalid_parameter", f"{name} values must be integers", field=name)
    if str(getattr(params, "smoothing", "ema") or "ema").lower() not in {"ema", "sma", "wma", "smma", "rma", "wilder"}:
        return ModuleResult.fail("invalid_parameter", "smoothing must be ema, sma, wma, smma, rma, or wilder", field="smoothing")
    slow_window, err = int_value("slow_window")
    if err is not None:
        return err
    fast_window, err = int_value("fast_window")
    if err is not None:
        return err
    if slow_window is not None and fast_window is not None and slow_window <= fast_window and indicator in {"macd", "ppo", "apo"}:
        return ModuleResult.fail("invalid_parameter", "slow_window must be greater than fast_window", field="slow_window")
    multiplier, err = float_value("multiplier")
    if err is not None:
        return err
    if multiplier is None or multiplier <= 0:
        return ModuleResult.fail("invalid_parameter", "multiplier must be positive", field="multiplier")
    vfactor, err = float_value("vfactor")
    if err is not None:
        return err
    if vfactor is None or vfactor <= 0 or vfactor > 1:
        return ModuleResult.fail("invalid_parameter", "vfactor must be in (0, 1]", field="vfactor")
    acceleration, err = float_value("acceleration")
    if err is not None:
        return err
    maximum, err = float_value("maximum")
    if err is not None:
        return err
    if acceleration is None or maximum is None or acceleration <= 0 or maximum <= 0:
        return ModuleResult.fail("invalid_parameter", "acceleration and maximum must be positive", field="acceleration")
    if maximum < acceleration:
        return ModuleResult.fail("invalid_parameter", "maximum must be greater than or equal to acceleration", field="maximum")
    mcginley_k, err = float_value("mcginley_k")
    if err is not None:
        return err
    if mcginley_k is None or mcginley_k <= 0:
        return ModuleResult.fail("invalid_parameter", "mcginley_k must be positive", field="mcginley_k")
    forecast_periods, err = int_value("forecast_periods")
    if err is not None:
        return err
    if forecast_periods is None or forecast_periods < 0:
        return ModuleResult.fail("invalid_parameter", "forecast_periods must be non-negative", field="forecast_periods")
    mama_slow_limit, err = float_value("mama_slow_limit")
    if err is not None:
        return err
    mama_fast_limit, err = float_value("mama_fast_limit")
    if err is not None:
        return err
    if mama_slow_limit is None or mama_fast_limit is None or not (0.0 < mama_slow_limit <= mama_fast_limit <= 1.0):
        return ModuleResult.fail("invalid_parameter", "MAMA limits must satisfy 0 < slow <= fast <= 1", field="mama_fast_limit")
    if str(getattr(params, "backend", "native") or "native").lower() not in {"native", "talib", "auto"}:
        return ModuleResult.fail("invalid_parameter", "backend must be native, talib, or auto", field="backend")
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


_TALIB_SUPPORTED = {
    "sma", "wma", "dema", "tema", "trima", "t3", "kama", "macd", "ppo", "apo",
    "adx", "adxr", "dmi", "aroon", "aroon_oscillator", "parabolic_sar", "mama",
    "ht_trendline", "ht_trendmode", "ht_sinewave", "ht_phasor",
    "ht_dominant_cycle_period", "ht_dominant_cycle_phase",
}


def _minimum_rows(indicator: str, p: TrendParams) -> int:
    w = int(p.window)
    if indicator in {"macd", "ppo", "apo"}:
        return int(p.slow_window) + int(p.signal_window) + 2
    if indicator in {"adx", "adxr", "dmi"}:
        return int(p.window) * 2 + 2
    if indicator in {"aroon", "aroon_oscillator"}:
        return int(p.window) + 1
    if indicator in {"ichimoku_cloud"}:
        return max(int(p.tenkan_window), int(p.kijun_window), int(p.senkou_b_window)) + int(p.displacement) + 1
    if indicator in {"gmma"}:
        return max(_periods(p.long_periods, [30, 35, 40, 45, 50, 60])) + 2
    if indicator in {"ma_ribbon"}:
        return max(_periods(p.periods, [5, 10, 20, 50, 100, 200]))
    if indicator.startswith("ht_") or indicator == "mama":
        return max(int(p.cycle_window), 48) + 5
    if indicator in {"supertrend", "keltner_channel", "chandelier_exit", "atr_trailing_stop"}:
        return max(int(p.atr_window), int(p.channel_window), w) + 2
    return max(w, int(getattr(p, "min_periods", 0) or 0), 2)


def _compute_talib(indicator: str, p: TrendParams, close: pd.Series, high: pd.Series, low: pd.Series, volume: Optional[pd.Series], talib: Any) -> _ComputeOutput:
    c = close.astype(float).to_numpy()
    h = high.astype(float).to_numpy()
    l = low.astype(float).to_numpy()
    n = int(p.window)
    if indicator == "sma":
        s = _series(talib.SMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "wma":
        s = _series(talib.WMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "dema":
        s = _series(talib.DEMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "tema":
        s = _series(talib.TEMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "trima":
        s = _series(talib.TRIMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "t3":
        s = _series(talib.T3(c, timeperiod=n, vfactor=float(p.vfactor)), close.index)
        return _single(indicator, close, s)
    if indicator == "kama":
        s = _series(talib.KAMA(c, timeperiod=n), close.index)
        return _single(indicator, close, s)
    if indicator == "macd":
        macd, sig, hist = talib.MACD(c, fastperiod=int(p.fast_window), slowperiod=int(p.slow_window), signalperiod=int(p.signal_window))
        return _macd_like("macd", close, _series(macd, close.index), _series(sig, close.index), _series(hist, close.index))
    if indicator == "ppo":
        ppo = _series(talib.PPO(c, fastperiod=int(p.fast_window), slowperiod=int(p.slow_window), matype=1), close.index)
        sig = _ema(ppo, int(p.signal_window), adjust=False, min_periods=int(p.signal_window))
        return _macd_like("ppo", close, ppo, sig, ppo - sig)
    if indicator == "apo":
        apo = _series(talib.APO(c, fastperiod=int(p.fast_window), slowperiod=int(p.slow_window), matype=1), close.index)
        sig = _ema(apo, int(p.signal_window), adjust=False, min_periods=int(p.signal_window))
        return _macd_like("apo", close, apo, sig, apo - sig)
    if indicator in {"adx", "adxr", "dmi"}:
        plus = _series(talib.PLUS_DI(h, l, c, timeperiod=n), close.index)
        minus = _series(talib.MINUS_DI(h, l, c, timeperiod=n), close.index)
        adx = _series(talib.ADX(h, l, c, timeperiod=n), close.index)
        if indicator == "adxr":
            adxr = _series(talib.ADXR(h, l, c, timeperiod=n), close.index)
            return _directional_output(indicator, close, adxr, plus, minus, adx=adx)
        if indicator == "adx":
            return _directional_output(indicator, close, adx, plus, minus, adx=adx)
        return _directional_output(indicator, close, plus - minus, plus, minus, adx=adx)
    if indicator in {"aroon", "aroon_oscillator"}:
        down, up = talib.AROON(h, l, timeperiod=n)
        up_s, down_s = _series(up, close.index), _series(down, close.index)
        osc = up_s - down_s
        return _aroon_output(indicator, close, up_s, down_s, osc)
    if indicator == "parabolic_sar":
        sar = _series(talib.SAR(h, l, acceleration=float(p.acceleration), maximum=float(p.maximum)), close.index)
        return _single(indicator, close, sar)
    if indicator == "mama":
        mama, fama = talib.MAMA(c, fastlimit=float(p.mama_fast_limit), slowlimit=float(p.mama_slow_limit))
        return _mama_output(close, _series(mama, close.index), _series(fama, close.index), native_note=False)
    if indicator.startswith("ht_"):
        return _talib_hilbert(indicator, close, c, talib)
    raise ValueError(f"unsupported talib indicator {indicator}")


def _compute_native(indicator: str, p: TrendParams, close: pd.Series, high: pd.Series, low: pd.Series, volume: Optional[pd.Series]) -> _ComputeOutput:
    n = int(p.window)
    if indicator == "sma":
        return _single(indicator, close, close.rolling(n, min_periods=_min_periods(p, n)).mean())
    if indicator == "wma":
        return _single(indicator, close, _wma(close, n, min_periods=_min_periods(p, n)))
    if indicator == "smma":
        return _single(indicator, close, _rma(close, n, min_periods=_min_periods(p, n)))
    if indicator == "dema":
        e1 = _ema(close, n, adjust=bool(p.adjust), min_periods=_min_periods(p, n))
        return _single(indicator, close, 2.0 * e1 - _ema(e1, n, adjust=bool(p.adjust), min_periods=_min_periods(p, n)))
    if indicator == "tema":
        e1 = _ema(close, n, adjust=bool(p.adjust), min_periods=_min_periods(p, n))
        e2 = _ema(e1, n, adjust=bool(p.adjust), min_periods=_min_periods(p, n))
        e3 = _ema(e2, n, adjust=bool(p.adjust), min_periods=_min_periods(p, n))
        return _single(indicator, close, 3.0 * e1 - 3.0 * e2 + e3)
    if indicator == "trima":
        return _single(indicator, close, _trima(close, n))
    if indicator == "t3":
        return _single(indicator, close, _t3(close, n, float(p.vfactor)))
    if indicator == "hma":
        half = max(1, n // 2)
        root = max(1, int(math.sqrt(n)))
        return _single(indicator, close, _wma(2.0 * _wma(close, half) - _wma(close, n), root))
    if indicator == "kama":
        return _single(indicator, close, _kama(close, n))
    if indicator == "zlema":
        lag = max(1, (n - 1) // 2)
        adjusted = close + (close - close.shift(lag))
        return _single(indicator, close, _ema(adjusted, n, adjust=False, min_periods=_min_periods(p, n)))
    if indicator == "mcginley_dynamic":
        return _single(indicator, close, _mcginley(close, n, float(p.mcginley_k)))
    if indicator == "vwma":
        if volume is None:
            raise ValueError("VWMA requires volume")
        num = (close * volume).rolling(n, min_periods=_min_periods(p, n)).sum()
        den = volume.rolling(n, min_periods=_min_periods(p, n)).sum().replace(0, np.nan)
        return _single(indicator, close, num / den)
    if indicator in {"macd", "ppo", "apo"}:
        fast = _ema(close, int(p.fast_window), adjust=bool(p.adjust), min_periods=int(p.fast_window))
        slow = _ema(close, int(p.slow_window), adjust=bool(p.adjust), min_periods=int(p.slow_window))
        base = (100.0 * (fast - slow) / slow.replace(0, np.nan)) if indicator == "ppo" else (fast - slow)
        sig = _ema(base, int(p.signal_window), adjust=bool(p.adjust), min_periods=int(p.signal_window))
        return _macd_like(indicator, close, base, sig, base - sig)
    if indicator in {"adx", "adxr", "dmi"}:
        plus, minus, adx = _dmi(high, low, close, n)
        if indicator == "adxr":
            return _directional_output(indicator, close, (adx + adx.shift(n)) / 2.0, plus, minus, adx=adx)
        if indicator == "adx":
            return _directional_output(indicator, close, adx, plus, minus, adx=adx)
        return _directional_output(indicator, close, plus - minus, plus, minus, adx=adx)
    if indicator in {"aroon", "aroon_oscillator"}:
        up, down = _aroon(high, low, n)
        return _aroon_output(indicator, close, up, down, up - down)
    if indicator == "vortex":
        vip, vin = _vortex(high, low, close, n)
        return _directional_output(indicator, close, vip - vin, vip, vin, adx=None)
    if indicator == "parabolic_sar":
        return _single(indicator, close, _parabolic_sar(high, low, float(p.acceleration), float(p.maximum)))
    if indicator == "supertrend":
        return _supertrend(high, low, close, int(p.atr_window), float(p.multiplier))
    if indicator == "donchian_channel":
        upper = high.rolling(int(p.channel_window), min_periods=int(p.channel_window)).max()
        lower = low.rolling(int(p.channel_window), min_periods=int(p.channel_window)).min()
        mid = (upper + lower) / 2.0
        return _channel_output(indicator, close, mid, upper, lower)
    if indicator == "keltner_channel":
        basis = _ema(close, n, adjust=False, min_periods=n)
        atr = _atr(high, low, close, int(p.atr_window))
        return _channel_output(indicator, close, basis, basis + float(p.multiplier) * atr, basis - float(p.multiplier) * atr)
    if indicator == "chandelier_exit":
        atr = _atr(high, low, close, int(p.atr_window))
        long_stop = high.rolling(int(p.channel_window), min_periods=int(p.channel_window)).max() - float(p.multiplier) * atr
        short_stop = low.rolling(int(p.channel_window), min_periods=int(p.channel_window)).min() + float(p.multiplier) * atr
        primary = pd.Series(np.where(close >= long_stop, long_stop, short_stop), index=close.index)
        return _stop_output(indicator, close, primary, long_stop, short_stop)
    if indicator == "atr_trailing_stop":
        return _atr_trailing_stop(high, low, close, int(p.atr_window), float(p.multiplier))
    if indicator == "ichimoku_cloud":
        return _ichimoku(high, low, close, p)
    if indicator == "alligator":
        return _alligator(close, p)
    if indicator == "ma_cross":
        fast = _ma(close, int(p.fast_window), str(p.smoothing), adjust=bool(p.adjust))
        slow = _ma(close, int(p.slow_window), str(p.smoothing), adjust=bool(p.adjust))
        return _cross_output(indicator, close, fast, slow)
    if indicator == "ma_ribbon":
        return _ribbon(close, _periods(p.periods, [5, 10, 20, 50, 100, 200]), str(p.smoothing))
    if indicator == "gmma":
        return _gmma(close, p)
    if indicator.startswith("linear_regression") or indicator in {"least_squares_moving_average", "time_series_forecast"}:
        return _regression_output(indicator, close, p)
    if indicator == "mama":
        mama, fama = _mama_native(close, p)
        return _mama_output(close, mama, fama, native_note=True)
    if indicator.startswith("ht_"):
        return _hilbert_native(indicator, close, p)
    if indicator == "trend_strength_index":
        return _trend_strength_index(close, p)
    if indicator == "chande_trend_meter":
        return _chande_trend_meter(high, low, close, p)
    raise ValueError(f"unsupported indicator {indicator}")


def _single(indicator: str, close: pd.Series, values: pd.Series) -> _ComputeOutput:
    return _ComputeOutput(
        primary=values,
        series={"value": values},
        signal=_cross_signal(close, values),
        trend_direction=_direction_from_price(close, values),
        trend_strength=_default_strength(close, values),
        summary={"calculation": indicator},
    )


def _macd_like(indicator: str, close: pd.Series, line: pd.Series, signal_line: pd.Series, hist: pd.Series) -> _ComputeOutput:
    sig = _last_relation_signal(line, signal_line)
    direction = "bullish" if sig in {"bullish", "cross_up"} else "bearish" if sig in {"bearish", "cross_down"} else "neutral"
    strength = _last_float(hist.abs())
    return _ComputeOutput(
        primary=line,
        series={"value": line, "signal_line": signal_line, "histogram": hist},
        signal=sig,
        trend_direction=direction,
        trend_strength=strength,
    )


def _directional_output(indicator: str, close: pd.Series, primary: pd.Series, plus: pd.Series, minus: pd.Series, *, adx: Optional[pd.Series]) -> _ComputeOutput:
    plus_last, minus_last = _last_float(plus), _last_float(minus)
    direction = "bullish" if (plus_last is not None and minus_last is not None and plus_last > minus_last) else "bearish" if (plus_last is not None and minus_last is not None and plus_last < minus_last) else "neutral"
    strength = _last_float(adx) if adx is not None else _last_float(primary.abs())
    series = {"value": primary, "plus": plus, "minus": minus}
    if adx is not None:
        series["adx"] = adx
    return _ComputeOutput(primary=primary, series=series, signal=direction, trend_direction=direction, trend_strength=strength)


def _aroon_output(indicator: str, close: pd.Series, up: pd.Series, down: pd.Series, osc: pd.Series) -> _ComputeOutput:
    direction = "bullish" if (_last_float(up) or 0.0) > (_last_float(down) or 0.0) else "bearish" if (_last_float(up) or 0.0) < (_last_float(down) or 0.0) else "neutral"
    primary = osc if indicator == "aroon_oscillator" else up
    return _ComputeOutput(primary=primary, series={"value": primary, "aroon_up": up, "aroon_down": down, "oscillator": osc}, signal=direction, trend_direction=direction, trend_strength=_last_float(osc.abs()))


def _channel_output(indicator: str, close: pd.Series, mid: pd.Series, upper: pd.Series, lower: pd.Series) -> _ComputeOutput:
    last_close, last_mid = _last_float(close), _last_float(mid)
    direction = "bullish" if last_close is not None and last_mid is not None and last_close > last_mid else "bearish" if last_close is not None and last_mid is not None and last_close < last_mid else "neutral"
    width = (upper - lower).abs()
    return _ComputeOutput(primary=mid, series={"value": mid, "upper": upper, "lower": lower, "width": width}, signal=direction, trend_direction=direction, trend_strength=_last_float((close - mid).abs() / width.replace(0, np.nan)))


def _stop_output(indicator: str, close: pd.Series, stop: pd.Series, long_stop: pd.Series, short_stop: pd.Series) -> _ComputeOutput:
    direction = _direction_from_price(close, stop)
    return _ComputeOutput(primary=stop, series={"value": stop, "long_stop": long_stop, "short_stop": short_stop}, signal=direction, trend_direction=direction, trend_strength=_default_strength(close, stop))


def _cross_output(indicator: str, close: pd.Series, fast: pd.Series, slow: pd.Series) -> _ComputeOutput:
    sig = _cross_signal(fast, slow)
    direction = "bullish" if (_last_float(fast) or 0.0) > (_last_float(slow) or 0.0) else "bearish" if (_last_float(fast) or 0.0) < (_last_float(slow) or 0.0) else "neutral"
    return _ComputeOutput(primary=fast - slow, series={"value": fast - slow, "fast": fast, "slow": slow}, signal=sig, trend_direction=direction, trend_strength=_last_float((fast - slow).abs()))


def _ma(series: pd.Series, n: int, mode: str, *, adjust: bool = False) -> pd.Series:
    mode = str(mode or "ema").lower()
    if mode == "sma":
        return series.rolling(n, min_periods=n).mean()
    if mode == "wma":
        return _wma(series, n)
    if mode in {"smma", "rma", "wilder"}:
        return _rma(series, n, min_periods=n)
    return _ema(series, n, adjust=adjust, min_periods=n)


def _ema(series: pd.Series, n: int, *, adjust: bool = False, min_periods: Optional[int] = None) -> pd.Series:
    return series.ewm(span=int(n), adjust=adjust, min_periods=int(min_periods if min_periods is not None else n)).mean()


def _rma(series: pd.Series, n: int, *, min_periods: Optional[int] = None) -> pd.Series:
    return series.ewm(alpha=1.0 / int(n), adjust=False, min_periods=int(min_periods if min_periods is not None else n)).mean()


def _wma(series: pd.Series, n: int, *, min_periods: Optional[int] = None) -> pd.Series:
    weights = np.arange(1, int(n) + 1, dtype=float)
    denom = float(weights.sum())
    mp = int(min_periods if min_periods is not None else n)
    return series.rolling(int(n), min_periods=mp).apply(lambda x: float(np.dot(x, weights[-len(x):]) / weights[-len(x):].sum()) if len(x) else np.nan, raw=True)


def _trima(series: pd.Series, n: int) -> pd.Series:
    n = int(n)
    if n % 2:
        k = (n + 1) // 2
        return series.rolling(k, min_periods=k).mean().rolling(k, min_periods=k).mean()
    return series.rolling(n // 2, min_periods=n // 2).mean().rolling(n // 2 + 1, min_periods=n // 2 + 1).mean()


def _t3(series: pd.Series, n: int, vfactor: float) -> pd.Series:
    e1 = _ema(series, n, min_periods=n)
    e2 = _ema(e1, n, min_periods=n)
    e3 = _ema(e2, n, min_periods=n)
    e4 = _ema(e3, n, min_periods=n)
    e5 = _ema(e4, n, min_periods=n)
    e6 = _ema(e5, n, min_periods=n)
    v = float(vfactor)
    c1 = -v ** 3
    c2 = 3 * v ** 2 + 3 * v ** 3
    c3 = -6 * v ** 2 - 3 * v - 3 * v ** 3
    c4 = 1 + 3 * v + v ** 3 + 3 * v ** 2
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3


def _kama(series: pd.Series, n: int, fast: int = 2, slow: int = 30) -> pd.Series:
    change = (series - series.shift(n)).abs()
    volatility = series.diff().abs().rolling(n, min_periods=n).sum()
    er = change / volatility.replace(0, np.nan)
    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    out = pd.Series(np.nan, index=series.index, dtype=float)
    vals = series.astype(float)
    for i, value in enumerate(vals):
        if pd.isna(value):
            continue
        if i == 0 or pd.isna(out.iloc[i - 1]):
            if i >= n:
                out.iloc[i] = value
        else:
            alpha = sc.iloc[i]
            if pd.isna(alpha):
                alpha = slow_sc ** 2
            out.iloc[i] = out.iloc[i - 1] + alpha * (value - out.iloc[i - 1])
    return out


def _mcginley(series: pd.Series, n: int, k: float) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    for i, price in enumerate(series.astype(float)):
        if pd.isna(price):
            continue
        if i == 0 or pd.isna(out.iloc[i - 1]) or out.iloc[i - 1] == 0:
            out.iloc[i] = price
            continue
        ratio = max(price / out.iloc[i - 1], 1e-12)
        out.iloc[i] = out.iloc[i - 1] + (price - out.iloc[i - 1]) / (float(k) * int(n) * ratio ** 4)
    return out


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return _rma(tr, int(n), min_periods=int(n))


def _dmi(high: pd.Series, low: pd.Series, close: pd.Series, n: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)
    atr = _atr(high, low, close, n)
    plus = 100.0 * _rma(plus_dm, n, min_periods=n) / atr.replace(0, np.nan)
    minus = 100.0 * _rma(minus_dm, n, min_periods=n) / atr.replace(0, np.nan)
    dx = 100.0 * (plus - minus).abs() / (plus + minus).replace(0, np.nan)
    adx = _rma(dx, n, min_periods=n)
    return plus, minus, adx


def _aroon(high: pd.Series, low: pd.Series, n: int) -> Tuple[pd.Series, pd.Series]:
    def up_func(x: np.ndarray) -> float:
        return 100.0 * (len(x) - 1 - int(np.argmax(x))) / max(len(x) - 1, 1)

    def down_func(x: np.ndarray) -> float:
        return 100.0 * (len(x) - 1 - int(np.argmin(x))) / max(len(x) - 1, 1)

    periods_since_high = high.rolling(n + 1, min_periods=n + 1).apply(up_func, raw=True)
    periods_since_low = low.rolling(n + 1, min_periods=n + 1).apply(down_func, raw=True)
    return 100.0 * (n - periods_since_high) / float(n), 100.0 * (n - periods_since_low) / float(n)


def _vortex(high: pd.Series, low: pd.Series, close: pd.Series, n: int) -> Tuple[pd.Series, pd.Series]:
    tr = pd.concat([(high - low).abs(), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    vip = (high - low.shift(1)).abs().rolling(n, min_periods=n).sum() / tr.rolling(n, min_periods=n).sum().replace(0, np.nan)
    vin = (low - high.shift(1)).abs().rolling(n, min_periods=n).sum() / tr.rolling(n, min_periods=n).sum().replace(0, np.nan)
    return vip, vin


def _parabolic_sar(high: pd.Series, low: pd.Series, acceleration: float, maximum: float) -> pd.Series:
    sar = pd.Series(np.nan, index=high.index, dtype=float)
    if len(high) < 2:
        return sar
    bull = bool(high.iloc[1] + low.iloc[1] >= high.iloc[0] + low.iloc[0])
    ep = high.iloc[0] if bull else low.iloc[0]
    sar.iloc[0] = low.iloc[0] if bull else high.iloc[0]
    af = float(acceleration)
    for i in range(1, len(high)):
        prev_sar = sar.iloc[i - 1]
        if pd.isna(prev_sar):
            prev_sar = low.iloc[i - 1] if bull else high.iloc[i - 1]
        curr = prev_sar + af * (ep - prev_sar)
        if bull:
            curr = min(curr, low.iloc[i - 1], low.iloc[i - 2] if i > 1 else low.iloc[i - 1])
            if low.iloc[i] < curr:
                bull = False
                curr = ep
                ep = low.iloc[i]
                af = float(acceleration)
            elif high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(float(maximum), af + float(acceleration))
        else:
            curr = max(curr, high.iloc[i - 1], high.iloc[i - 2] if i > 1 else high.iloc[i - 1])
            if high.iloc[i] > curr:
                bull = True
                curr = ep
                ep = high.iloc[i]
                af = float(acceleration)
            elif low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(float(maximum), af + float(acceleration))
        sar.iloc[i] = curr
    return sar


def _supertrend(high: pd.Series, low: pd.Series, close: pd.Series, atr_n: int, multiplier: float) -> _ComputeOutput:
    atr = _atr(high, low, close, atr_n)
    hl2 = (high + low) / 2.0
    upper_basic = hl2 + multiplier * atr
    lower_basic = hl2 - multiplier * atr
    upper = upper_basic.copy()
    lower = lower_basic.copy()
    trend = pd.Series(np.nan, index=close.index, dtype=float)
    st = pd.Series(np.nan, index=close.index, dtype=float)
    for i in range(1, len(close)):
        upper.iloc[i] = upper_basic.iloc[i] if pd.isna(upper.iloc[i - 1]) or close.iloc[i - 1] > upper.iloc[i - 1] else min(upper_basic.iloc[i], upper.iloc[i - 1])
        lower.iloc[i] = lower_basic.iloc[i] if pd.isna(lower.iloc[i - 1]) or close.iloc[i - 1] < lower.iloc[i - 1] else max(lower_basic.iloc[i], lower.iloc[i - 1])
        if pd.isna(st.iloc[i - 1]):
            trend.iloc[i] = 1.0 if close.iloc[i] >= hl2.iloc[i] else -1.0
        elif st.iloc[i - 1] == upper.iloc[i - 1]:
            trend.iloc[i] = 1.0 if close.iloc[i] > upper.iloc[i] else -1.0
        else:
            trend.iloc[i] = -1.0 if close.iloc[i] < lower.iloc[i] else 1.0
        st.iloc[i] = lower.iloc[i] if trend.iloc[i] > 0 else upper.iloc[i]
    direction = "bullish" if (_last_float(trend) or 0.0) > 0 else "bearish"
    return _ComputeOutput(primary=st, series={"value": st, "upper": upper, "lower": lower, "trend": trend}, signal=direction, trend_direction=direction, trend_strength=_default_strength(close, st))


def _atr_trailing_stop(high: pd.Series, low: pd.Series, close: pd.Series, atr_n: int, multiplier: float) -> _ComputeOutput:
    atr = _atr(high, low, close, atr_n)
    long_stop = close - multiplier * atr
    short_stop = close + multiplier * atr
    stop = pd.Series(np.nan, index=close.index, dtype=float)
    trend = pd.Series(np.nan, index=close.index, dtype=float)
    for i in range(1, len(close)):
        prev_stop = stop.iloc[i - 1]
        prev_trend = trend.iloc[i - 1]
        if pd.isna(prev_stop):
            trend.iloc[i] = 1.0
            stop.iloc[i] = long_stop.iloc[i]
        elif prev_trend >= 0:
            stop.iloc[i] = max(long_stop.iloc[i], prev_stop)
            trend.iloc[i] = -1.0 if close.iloc[i] < stop.iloc[i] else 1.0
            if trend.iloc[i] < 0:
                stop.iloc[i] = short_stop.iloc[i]
        else:
            stop.iloc[i] = min(short_stop.iloc[i], prev_stop)
            trend.iloc[i] = 1.0 if close.iloc[i] > stop.iloc[i] else -1.0
            if trend.iloc[i] > 0:
                stop.iloc[i] = long_stop.iloc[i]
    direction = "bullish" if (_last_float(trend) or 0.0) > 0 else "bearish"
    return _ComputeOutput(primary=stop, series={"value": stop, "long_stop": long_stop, "short_stop": short_stop, "trend": trend}, signal=direction, trend_direction=direction, trend_strength=_default_strength(close, stop))


def _ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, p: TrendParams) -> _ComputeOutput:
    tenkan = (high.rolling(int(p.tenkan_window), min_periods=int(p.tenkan_window)).max() + low.rolling(int(p.tenkan_window), min_periods=int(p.tenkan_window)).min()) / 2.0
    kijun = (high.rolling(int(p.kijun_window), min_periods=int(p.kijun_window)).max() + low.rolling(int(p.kijun_window), min_periods=int(p.kijun_window)).min()) / 2.0
    span_a = ((tenkan + kijun) / 2.0).shift(int(p.displacement))
    span_b = ((high.rolling(int(p.senkou_b_window), min_periods=int(p.senkou_b_window)).max() + low.rolling(int(p.senkou_b_window), min_periods=int(p.senkou_b_window)).min()) / 2.0).shift(int(p.displacement))
    chikou = close.shift(-int(p.displacement))
    cloud_mid = (span_a + span_b) / 2.0
    direction = _direction_from_price(close, cloud_mid)
    return _ComputeOutput(primary=cloud_mid, series={"value": cloud_mid, "tenkan": tenkan, "kijun": kijun, "senkou_a": span_a, "senkou_b": span_b, "chikou": chikou}, signal=direction, trend_direction=direction, trend_strength=_default_strength(close, cloud_mid))


def _alligator(close: pd.Series, p: TrendParams) -> _ComputeOutput:
    jaw = _rma(close, int(p.jaw_window), min_periods=int(p.jaw_window)).shift(int(p.jaw_shift))
    teeth = _rma(close, int(p.teeth_window), min_periods=int(p.teeth_window)).shift(int(p.teeth_shift))
    lips = _rma(close, int(p.lips_window), min_periods=int(p.lips_window)).shift(int(p.lips_shift))
    spread = lips - jaw
    direction = "bullish" if (_last_float(lips) or 0.0) > (_last_float(teeth) or 0.0) > (_last_float(jaw) or 0.0) else "bearish" if (_last_float(lips) or 0.0) < (_last_float(teeth) or 0.0) < (_last_float(jaw) or 0.0) else "neutral"
    return _ComputeOutput(primary=spread, series={"value": spread, "jaw": jaw, "teeth": teeth, "lips": lips}, signal=direction, trend_direction=direction, trend_strength=_last_float(spread.abs()))


def _ribbon(close: pd.Series, periods: List[int], smoothing: str) -> _ComputeOutput:
    values = {f"ma_{p}": _ma(close, int(p), smoothing) for p in periods}
    ordered = [values[f"ma_{p}"] for p in periods]
    spread = ordered[0] - ordered[-1]
    last_vals = [_last_float(x) for x in ordered]
    if all(v is not None for v in last_vals):
        bullish = all(last_vals[i] >= last_vals[i + 1] for i in range(len(last_vals) - 1))
        bearish = all(last_vals[i] <= last_vals[i + 1] for i in range(len(last_vals) - 1))
    else:
        bullish = bearish = False
    direction = "bullish" if bullish else "bearish" if bearish else "mixed"
    values["value"] = spread
    return _ComputeOutput(primary=spread, series=values, signal=direction, trend_direction=direction, trend_strength=_last_float(spread.abs()))


def _gmma(close: pd.Series, p: TrendParams) -> _ComputeOutput:
    short = _periods(p.short_periods, [3, 5, 8, 10, 12, 15])
    long = _periods(p.long_periods, [30, 35, 40, 45, 50, 60])
    s_vals = {f"short_{x}": _ema(close, x, min_periods=x) for x in short}
    l_vals = {f"long_{x}": _ema(close, x, min_periods=x) for x in long}
    s_avg = pd.concat(s_vals.values(), axis=1).mean(axis=1)
    l_avg = pd.concat(l_vals.values(), axis=1).mean(axis=1)
    spread = s_avg - l_avg
    direction = "bullish" if (_last_float(spread) or 0.0) > 0 else "bearish" if (_last_float(spread) or 0.0) < 0 else "neutral"
    series = {"value": spread, "short_average": s_avg, "long_average": l_avg, **s_vals, **l_vals}
    return _ComputeOutput(primary=spread, series=series, signal=direction, trend_direction=direction, trend_strength=_last_float(spread.abs()))


def _regression_output(indicator: str, close: pd.Series, p: TrendParams) -> _ComputeOutput:
    n = int(p.window)
    reg, slope, intercept, r2 = _rolling_regression(close, n)
    forecast = reg + slope * int(p.forecast_periods)
    angle = np.degrees(np.arctan(slope))
    if indicator == "linear_regression_slope":
        primary = slope
    elif indicator == "linear_regression_angle":
        primary = angle
    elif indicator == "linear_regression_r2":
        primary = r2
    elif indicator == "time_series_forecast":
        primary = forecast
    else:
        primary = reg
    direction = "bullish" if (_last_float(slope) or 0.0) > 0 else "bearish" if (_last_float(slope) or 0.0) < 0 else "neutral"
    return _ComputeOutput(primary=primary, series={"value": primary, "regression": reg, "slope": slope, "intercept": intercept, "r2": r2, "forecast": forecast, "angle": angle}, signal=direction, trend_direction=direction, trend_strength=_last_float(r2))


def _rolling_regression(series: pd.Series, n: int) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    x = np.arange(n, dtype=float)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()

    def calc(y: np.ndarray, idx: int) -> float:
        if np.isnan(y).any():
            return np.nan
        y_mean = y.mean()
        slope = float(((x - x_mean) * (y - y_mean)).sum() / x_var)
        intercept = float(y_mean - slope * x_mean)
        pred = intercept + slope * x
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y_mean) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        vals = [intercept + slope * (n - 1), slope, intercept, r2]
        return vals[idx]

    reg = series.rolling(n, min_periods=n).apply(lambda y: calc(y, 0), raw=True)
    slope = series.rolling(n, min_periods=n).apply(lambda y: calc(y, 1), raw=True)
    intercept = series.rolling(n, min_periods=n).apply(lambda y: calc(y, 2), raw=True)
    r2 = series.rolling(n, min_periods=n).apply(lambda y: calc(y, 3), raw=True)
    return reg, slope, intercept, r2


def _mama_native(close: pd.Series, p: TrendParams) -> Tuple[pd.Series, pd.Series]:
    er = (close - close.shift(int(p.window))).abs() / close.diff().abs().rolling(int(p.window), min_periods=int(p.window)).sum().replace(0, np.nan)
    alpha = (float(p.mama_slow_limit) + er.fillna(0.0) * (float(p.mama_fast_limit) - float(p.mama_slow_limit))).clip(float(p.mama_slow_limit), float(p.mama_fast_limit))
    mama = pd.Series(np.nan, index=close.index, dtype=float)
    for i, price in enumerate(close.astype(float)):
        if pd.isna(price):
            continue
        if i == 0 or pd.isna(mama.iloc[i - 1]):
            mama.iloc[i] = price if i >= int(p.window) else np.nan
        else:
            mama.iloc[i] = alpha.iloc[i] * price + (1.0 - alpha.iloc[i]) * mama.iloc[i - 1]
    fama = mama.ewm(alpha=0.5 * float(p.mama_slow_limit), adjust=False, min_periods=int(p.window)).mean()
    return mama, fama


def _mama_output(close: pd.Series, mama: pd.Series, fama: pd.Series, *, native_note: bool) -> _ComputeOutput:
    sig = _cross_signal(mama, fama)
    direction = "bullish" if (_last_float(mama) or 0.0) > (_last_float(fama) or 0.0) else "bearish" if (_last_float(mama) or 0.0) < (_last_float(fama) or 0.0) else "neutral"
    return _ComputeOutput(primary=mama, series={"value": mama, "mama": mama, "fama": fama}, signal=sig, trend_direction=direction, trend_strength=_last_float((mama - fama).abs()), diagnostics={"native_approximation": native_note})


def _talib_hilbert(indicator: str, close: pd.Series, c: np.ndarray, talib: Any) -> _ComputeOutput:
    if indicator == "ht_trendline":
        s = _series(talib.HT_TRENDLINE(c), close.index)
        return _single(indicator, close, s)
    if indicator == "ht_trendmode":
        s = _series(talib.HT_TRENDMODE(c), close.index)
        return _ComputeOutput(primary=s, series={"value": s}, signal="trend" if (_last_float(s) or 0.0) > 0 else "cycle", trend_direction="trend" if (_last_float(s) or 0.0) > 0 else "cycle", trend_strength=_last_float(s))
    if indicator == "ht_sinewave":
        sine, lead = talib.HT_SINE(c)
        sine_s, lead_s = _series(sine, close.index), _series(lead, close.index)
        return _cross_output(indicator, close, sine_s, lead_s)
    if indicator == "ht_phasor":
        inphase, quad = talib.HT_PHASOR(c)
        inp, q = _series(inphase, close.index), _series(quad, close.index)
        return _ComputeOutput(primary=inp, series={"value": inp, "inphase": inp, "quadrature": q}, signal=_last_relation_signal(inp, q), trend_direction="bullish" if (_last_float(inp) or 0.0) > 0 else "bearish", trend_strength=_last_float((inp.pow(2) + q.pow(2)).pow(0.5)))
    if indicator == "ht_dominant_cycle_period":
        s = _series(talib.HT_DCPERIOD(c), close.index)
        return _ComputeOutput(primary=s, series={"value": s}, trend_direction="cycle", trend_strength=_last_float(s))
    if indicator == "ht_dominant_cycle_phase":
        s = _series(talib.HT_DCPHASE(c), close.index)
        return _ComputeOutput(primary=s, series={"value": s}, trend_direction="cycle", trend_strength=_last_float(s.abs()))
    raise ValueError(indicator)


def _hilbert_native(indicator: str, close: pd.Series, p: TrendParams) -> _ComputeOutput:
    n = int(p.cycle_window)
    trendline = _ema(close, max(4, n // 2), adjust=False, min_periods=max(4, n // 2))
    detrended = close - trendline
    quadrature = detrended.diff().rolling(3, min_periods=1).mean()
    phase = np.degrees(np.arctan2(quadrature, detrended.replace(0, np.nan)))
    sine = np.sin(np.radians(phase))
    lead = np.sin(np.radians(phase + 45.0))
    period = _dominant_period(close, n)
    mode_raw = (trendline.diff().abs().rolling(n, min_periods=n).mean() / close.diff().abs().rolling(n, min_periods=n).mean().replace(0, np.nan)).clip(0, 1)
    mode = (mode_raw > 0.35).astype(float)
    diag = {"native_approximation": True, "approximation_note": "Ehlers/Hilbert native mode is a lightweight phase/trend approximation; use backend='talib' for TA-Lib parity."}
    if indicator == "ht_trendline":
        return _ComputeOutput(primary=trendline, series={"value": trendline}, signal=_cross_signal(close, trendline), trend_direction=_direction_from_price(close, trendline), trend_strength=_default_strength(close, trendline), diagnostics=diag)
    if indicator == "ht_trendmode":
        return _ComputeOutput(primary=mode, series={"value": mode}, signal="trend" if (_last_float(mode) or 0.0) > 0 else "cycle", trend_direction="trend" if (_last_float(mode) or 0.0) > 0 else "cycle", trend_strength=_last_float(mode), diagnostics=diag)
    if indicator == "ht_sinewave":
        return _ComputeOutput(primary=sine, series={"value": sine, "sine": sine, "lead_sine": lead}, signal=_cross_signal(sine, lead), trend_direction="cycle", trend_strength=_last_float(sine.abs()), diagnostics=diag)
    if indicator == "ht_phasor":
        return _ComputeOutput(primary=detrended, series={"value": detrended, "inphase": detrended, "quadrature": quadrature}, signal=_last_relation_signal(detrended, quadrature), trend_direction="cycle", trend_strength=_last_float((detrended.pow(2) + quadrature.pow(2)).pow(0.5)), diagnostics=diag)
    if indicator == "ht_dominant_cycle_period":
        return _ComputeOutput(primary=period, series={"value": period}, signal="cycle", trend_direction="cycle", trend_strength=_last_float(period), diagnostics=diag)
    if indicator == "ht_dominant_cycle_phase":
        return _ComputeOutput(primary=phase, series={"value": phase}, signal="cycle", trend_direction="cycle", trend_strength=_last_float(phase.abs()), diagnostics=diag)
    raise ValueError(indicator)


def _dominant_period(close: pd.Series, n: int) -> pd.Series:
    min_lag, max_lag = 10, max(12, min(48, n))
    out = pd.Series(np.nan, index=close.index, dtype=float)
    vals = close.astype(float)
    for i in range(n, len(vals)):
        window = vals.iloc[i - n + 1:i + 1].dropna()
        if len(window) < n:
            continue
        best_lag, best_corr = min_lag, -np.inf
        for lag in range(min_lag, max_lag + 1):
            a = window.iloc[lag:].to_numpy()
            b = window.iloc[:-lag].to_numpy()
            if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
                continue
            corr = float(np.corrcoef(a, b)[0, 1])
            if corr > best_corr:
                best_corr, best_lag = corr, lag
        out.iloc[i] = float(best_lag)
    return out


def _trend_strength_index(close: pd.Series, p: TrendParams) -> _ComputeOutput:
    reg, slope, _, r2 = _rolling_regression(close, int(p.window))
    vol = close.diff().abs().rolling(int(p.window), min_periods=int(p.window)).mean().replace(0, np.nan)
    signed = 100.0 * (slope / vol).clip(-1, 1) * r2.clip(0, 1)
    direction = "bullish" if (_last_float(signed) or 0.0) > 0 else "bearish" if (_last_float(signed) or 0.0) < 0 else "neutral"
    return _ComputeOutput(primary=signed, series={"value": signed, "regression": reg, "slope": slope, "r2": r2}, signal=direction, trend_direction=direction, trend_strength=abs(_last_float(signed) or 0.0))


def _chande_trend_meter(high: pd.Series, low: pd.Series, close: pd.Series, p: TrendParams) -> _ComputeOutput:
    ema_fast = _ema(close, int(p.fast_window), min_periods=int(p.fast_window))
    ema_slow = _ema(close, int(p.slow_window), min_periods=int(p.slow_window))
    plus, minus, adx = _dmi(high, low, close, int(p.atr_window))
    roc = close.pct_change(int(p.window)) * 100.0
    rsi = _rsi(close, int(p.window))
    score = pd.Series(0.0, index=close.index)
    score += np.where(close > ema_slow, 20.0, 0.0)
    score += np.where(ema_fast > ema_slow, 20.0, 0.0)
    score += np.where(plus > minus, 20.0, 0.0)
    score += np.where(adx > 20.0, 20.0, 0.0)
    score += np.where((roc > 0.0) & (rsi > 50.0), 20.0, 0.0)
    direction = "bullish" if (_last_float(score) or 0.0) >= 60 else "bearish" if (_last_float(score) or 0.0) <= 40 else "neutral"
    return _ComputeOutput(primary=score, series={"value": score, "ema_fast": ema_fast, "ema_slow": ema_slow, "adx": adx, "roc": roc, "rsi": rsi}, signal=direction, trend_direction=direction, trend_strength=_last_float(score), diagnostics={"score_components": ["close>slow_ema", "fast_ema>slow_ema", "plus_di>minus_di", "adx>20", "roc>0 and rsi>50"]})


def _rsi(close: pd.Series, n: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    rs = _rma(gain, n, min_periods=n) / _rma(loss, n, min_periods=n).replace(0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _periods(value: Optional[List[int]], default: List[int]) -> List[int]:
    vals = value if value else default
    out = sorted({int(x) for x in vals if int(x) > 0})
    return out or list(default)


def _min_periods(p: TrendParams, n: int) -> int:
    return int(p.min_periods if p.min_periods is not None else n)


def _series(values: Any, index: Any) -> pd.Series:
    return pd.Series(values, index=index, dtype=float)


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series.tolist()]


def _last_float(series: pd.Series) -> Optional[float]:
    valid = series.dropna()
    if valid.empty:
        return None
    value = float(valid.iloc[-1])
    return value if math.isfinite(value) else None


def _direction_from_price(price: pd.Series, ref: pd.Series) -> str:
    p, r = _last_float(price), _last_float(ref)
    if p is None or r is None:
        return "unknown"
    if p > r:
        return "bullish"
    if p < r:
        return "bearish"
    return "neutral"


def _default_strength(price: pd.Series, ref: pd.Series) -> Optional[float]:
    p, r = _last_float(price), _last_float(ref)
    if p is None or r is None or p == 0:
        return None
    return abs((p - r) / p)


def _cross_signal(a: pd.Series, b: pd.Series) -> str:
    diff = a - b
    valid = diff.dropna()
    if len(valid) < 2:
        return _last_relation_signal(a, b)
    prev, curr = float(valid.iloc[-2]), float(valid.iloc[-1])
    if prev <= 0 < curr:
        return "cross_up"
    if prev >= 0 > curr:
        return "cross_down"
    return "bullish" if curr > 0 else "bearish" if curr < 0 else "neutral"


def _last_relation_signal(a: pd.Series, b: pd.Series) -> str:
    av, bv = _last_float(a), _last_float(b)
    if av is None or bv is None:
        return "none"
    if av > bv:
        return "bullish"
    if av < bv:
        return "bearish"
    return "neutral"


__all__ = [
    "TrendParams",
    "TrendReport",
    "normalize_trend_input",
    "run_trend_indicator",
]
