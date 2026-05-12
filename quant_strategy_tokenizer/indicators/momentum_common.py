"""
quant_strategy_tokenizer.indicators.momentum_common
===================================================
Purpose: shared implementation layer for atomic momentum indicator tokens.
Core idea: Normalize caller-supplied price/OHLC/OHLCV data, validate oscillator
parameters, optionally delegate supported calculations to TA-Lib, and return a
uniform MomentumReport. Assumes momentum tokens should expose speed, exhaustion,
and oscillator-state semantics without owning data sourcing or execution.
Inputs: raw user data, DataFrameSpec/ExtractorSpec, MomentumParams-compatible
configuration, indicator name, input kind, and ModuleRunContext.
Outputs: MomentumReport wrapped in ModuleResult with last values, direction,
strength, zone, optional series, diagnostics, warnings, and report files.
Failure semantics: invalid params, missing fields, insufficient history,
unsupported backend, unavailable TA-Lib, and calculation errors return
ModuleResult.fail.
Market generalization: all calculations operate on caller-mapped numeric fields
and do not assume asset class, venue, session model, or symbol format.
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
class MomentumParams:
    """Generic momentum-indicator options used by atomic wrapper modules.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`. Native uses pandas/numpy. Talib
      requires TA-Lib and fails explicitly if unavailable. Auto uses TA-Lib
      only for supported functions when installed.
    - `value_field`, `volume_field`: logical fields resolved through
      DataFrameSpec.
    - window fields: per-indicator lookbacks in rows/bars. Unused fields are
      ignored by each indicator but kept for a stable interface.
    - `overbought`, `oversold`: zone thresholds used for report semantics.
    """

    backend: str = "native"
    value_field: str = "close"
    volume_field: str = "volume"
    window: int = 14
    min_periods: Optional[int] = None
    fast_window: int = 12
    slow_window: int = 26
    signal_window: int = 9
    smooth_window: int = 3
    smooth_k: int = 3
    smooth_d: int = 3
    short_window: int = 7
    medium_window: int = 14
    long_window: int = 28
    roc_window: int = 10
    rsi_window: int = 14
    stoch_window: int = 14
    rank_window: int = 100
    streak_rsi_window: int = 2
    momentum_window: int = 5
    cci_constant: float = 0.015
    overbought: float = 70.0
    oversold: float = 30.0
    scalar: float = 100.0


@dataclass
class MomentumReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    momentum_direction: str = "unknown"
    momentum_strength: Optional[float] = None
    signal: str = "none"
    zone: str = "unknown"
    overbought: Optional[float] = None
    oversold: Optional[float] = None
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
    momentum_direction: str = "unknown"
    momentum_strength: Optional[float] = None
    zone: str = "unknown"
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_momentum_input(request: Any, input_kind: str) -> ModuleResult[Any]:
    params = request.params
    value_field = str(getattr(params, "value_field", "close") or "close")
    volume_field = str(getattr(params, "volume_field", "volume") or "volume")
    if input_kind == "price":
        required = [value_field]
    elif input_kind == "ohlc":
        required = ["high", "low", "close"]
    elif input_kind == "ohlc_open":
        required = ["open", "high", "low", "close"]
    elif input_kind == "ohlcv":
        required = ["high", "low", "close", volume_field]
    else:
        required = [value_field]
    return normalize_frame(request.data, required_fields=required, optional_fields=[], spec=request.spec, extractor=request.extractor)


def run_momentum_indicator(indicator: str, request: Any, *, input_kind: str, module_name: str) -> ModuleResult[MomentumReport]:
    params = request.params
    param_error = _validate_params(indicator, params)
    if param_error is not None:
        return param_error

    backend_result = _resolve_backend(str(getattr(params, "backend", "native") or "native"), indicator)
    if not backend_result.ok:
        return ModuleResult.fail(backend_result.failure.kind, backend_result.failure.message, details=backend_result.failure.details)
    backend, talib_mod = backend_result.value

    norm = normalize_momentum_input(request, input_kind)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")

    frame = nf.frame
    used = dict(nf.used_fields)
    close_col = used.get(str(getattr(params, "value_field", "close") or "close")) or used.get("close")
    if close_col is None:
        return ModuleResult.fail("missing_required_field", "momentum indicator needs a resolved price field")
    close = pd.to_numeric(frame[close_col], errors="coerce")
    open_ = pd.to_numeric(frame[used["open"]], errors="coerce") if "open" in used else close
    high = pd.to_numeric(frame[used["high"]], errors="coerce") if "high" in used else close
    low = pd.to_numeric(frame[used["low"]], errors="coerce") if "low" in used else close
    volume_col = used.get(str(getattr(params, "volume_field", "volume") or "volume"))
    volume = pd.to_numeric(frame[volume_col], errors="coerce") if volume_col is not None else None

    min_rows = _minimum_rows(indicator, params)
    numeric_rows = int(close.dropna().shape[0])
    if numeric_rows < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} numeric rows, got {numeric_rows}")

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

    ob = float(getattr(params, "overbought", 70.0))
    os = float(getattr(params, "oversold", 30.0))
    zone = computed.zone if computed.zone != "unknown" else _zone(last, ob, os)
    direction = computed.momentum_direction
    if direction == "unknown":
        direction = _direction_from_level(last, ob, os)
    strength = computed.momentum_strength
    if strength is None:
        strength = _default_strength(last, ob, os)

    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = MomentumReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        momentum_direction=direction,
        momentum_strength=strength,
        signal=computed.signal,
        zone=zone,
        overbought=ob,
        oversold=os,
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


def _validate_params(indicator: str, params: MomentumParams) -> Optional[ModuleResult[MomentumReport]]:
    int_fields = [
        "window", "fast_window", "slow_window", "signal_window", "smooth_window", "smooth_k", "smooth_d",
        "short_window", "medium_window", "long_window", "roc_window", "rsi_window", "stoch_window",
        "rank_window", "streak_rsi_window", "momentum_window",
    ]
    for name in int_fields:
        try:
            value = int(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if params.min_periods is not None:
        try:
            if int(params.min_periods) <= 0:
                return ModuleResult.fail("invalid_parameter", "min_periods must be positive when provided", field="min_periods")
        except Exception:
            return ModuleResult.fail("invalid_parameter", "min_periods must be an integer", field="min_periods")
    for name in ("cci_constant", "scalar"):
        try:
            value = float(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    for name in ("overbought", "oversold"):
        try:
            float(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)
    if str(getattr(params, "backend", "native") or "native").lower() not in {"native", "talib", "auto"}:
        return ModuleResult.fail("invalid_parameter", "backend must be native, talib, or auto", field="backend")
    if indicator in {"stochastic_oscillator", "stochastic_fast", "stochastic_rsi", "stochastic_momentum_index"}:
        if int(params.smooth_k) <= 0 or int(params.smooth_d) <= 0:
            return ModuleResult.fail("invalid_parameter", "smooth_k and smooth_d must be positive", field="smooth_k")
    if indicator in {"kst"} and not (int(params.short_window) < int(params.medium_window) < int(params.long_window)):
        return ModuleResult.fail("invalid_parameter", "KST windows must satisfy short < medium < long", field="long_window")
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
    "rsi", "stochastic_oscillator", "stochastic_fast", "stochastic_rsi", "cci", "cmo",
    "momentum", "roc", "rocp", "rocr", "rocr100", "williams_r", "ultimate_oscillator",
    "trix", "bop", "mfi",
}


def _minimum_rows(indicator: str, p: MomentumParams) -> int:
    w = int(p.window)
    if indicator in {"ultimate_oscillator"}:
        return max(int(p.short_window), int(p.medium_window), int(p.long_window)) + 2
    if indicator in {"kst"}:
        return int(p.long_window) + int(p.signal_window) + int(p.smooth_window) + 5
    if indicator in {"connors_rsi"}:
        return max(int(p.rsi_window), int(p.rank_window) + int(p.roc_window), int(p.streak_rsi_window)) + 3
    if indicator in {"awesome_oscillator", "accelerator_oscillator"}:
        return max(int(p.fast_window), int(p.slow_window)) + int(p.signal_window) + 2
    if indicator in {"coppock_curve"}:
        return max(int(p.short_window), int(p.long_window)) + w + 2
    if indicator in {"stochastic_oscillator", "stochastic_fast", "stochastic_rsi", "stochastic_momentum_index", "kdj"}:
        return int(p.stoch_window) + int(p.smooth_k) + int(p.smooth_d) + 2
    if indicator in {"relative_momentum_index"}:
        return int(p.window) + int(p.momentum_window) + 2
    if indicator in {"trix"}:
        return w * 3 + 2
    return max(w, int(getattr(p, "min_periods", 0) or 0), 2)


def _compute_talib(indicator: str, p: MomentumParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: Optional[pd.Series], talib: Any) -> _ComputeOutput:
    o = open_.astype(float).to_numpy()
    h = high.astype(float).to_numpy()
    l = low.astype(float).to_numpy()
    c = close.astype(float).to_numpy()
    v = volume.astype(float).to_numpy() if volume is not None else None
    n = int(p.window)
    if indicator == "rsi":
        return _osc_output(indicator, _series(talib.RSI(c, timeperiod=n), close.index), p)
    if indicator == "stochastic_oscillator":
        k, d = talib.STOCH(h, l, c, fastk_period=int(p.stoch_window), slowk_period=int(p.smooth_k), slowk_matype=0, slowd_period=int(p.smooth_d), slowd_matype=0)
        return _two_line_output(indicator, _series(k, close.index), _series(d, close.index), p, "percent_k", "percent_d")
    if indicator == "stochastic_fast":
        k, d = talib.STOCHF(h, l, c, fastk_period=int(p.stoch_window), fastd_period=int(p.smooth_d), fastd_matype=0)
        return _two_line_output(indicator, _series(k, close.index), _series(d, close.index), p, "fast_k", "fast_d")
    if indicator == "stochastic_rsi":
        k, d = talib.STOCHRSI(c, timeperiod=int(p.rsi_window), fastk_period=int(p.stoch_window), fastd_period=int(p.smooth_d), fastd_matype=0)
        return _two_line_output(indicator, _series(k, close.index), _series(d, close.index), p, "stoch_rsi_k", "stoch_rsi_d")
    if indicator == "cci":
        return _osc_output(indicator, _series(talib.CCI(h, l, c, timeperiod=n), close.index), p)
    if indicator == "cmo":
        return _osc_output(indicator, _series(talib.CMO(c, timeperiod=n), close.index), p)
    if indicator == "momentum":
        return _zero_output(indicator, _series(talib.MOM(c, timeperiod=n), close.index))
    if indicator == "roc":
        return _zero_output(indicator, _series(talib.ROC(c, timeperiod=n), close.index))
    if indicator == "rocp":
        return _zero_output(indicator, _series(talib.ROCP(c, timeperiod=n), close.index))
    if indicator == "rocr":
        return _ratio_output(indicator, _series(talib.ROCR(c, timeperiod=n), close.index))
    if indicator == "rocr100":
        return _ratio_output(indicator, _series(talib.ROCR100(c, timeperiod=n), close.index), mid=100.0)
    if indicator == "williams_r":
        return _osc_output(indicator, _series(talib.WILLR(h, l, c, timeperiod=n), close.index), p)
    if indicator == "ultimate_oscillator":
        uo = talib.ULTOSC(h, l, c, timeperiod1=int(p.short_window), timeperiod2=int(p.medium_window), timeperiod3=int(p.long_window))
        return _osc_output(indicator, _series(uo, close.index), p)
    if indicator == "trix":
        return _zero_output(indicator, _series(talib.TRIX(c, timeperiod=n), close.index))
    if indicator == "bop":
        return _zero_output(indicator, _series(talib.BOP(o, h, l, c), close.index))
    if indicator == "mfi":
        if v is None:
            raise ValueError("MFI requires volume")
        return _osc_output(indicator, _series(talib.MFI(h, l, c, v, timeperiod=n), close.index), p)
    raise ValueError(f"unsupported talib indicator {indicator}")


def _compute_native(indicator: str, p: MomentumParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, volume: Optional[pd.Series]) -> _ComputeOutput:
    n = int(p.window)
    if indicator == "rsi":
        return _osc_output(indicator, _rsi(close, n), p)
    if indicator == "stochastic_oscillator":
        k = _stoch_k(high, low, close, int(p.stoch_window)).rolling(int(p.smooth_k), min_periods=int(p.smooth_k)).mean()
        d = k.rolling(int(p.smooth_d), min_periods=int(p.smooth_d)).mean()
        return _two_line_output(indicator, k, d, p, "percent_k", "percent_d")
    if indicator == "stochastic_fast":
        k = _stoch_k(high, low, close, int(p.stoch_window))
        d = k.rolling(int(p.smooth_d), min_periods=int(p.smooth_d)).mean()
        return _two_line_output(indicator, k, d, p, "fast_k", "fast_d")
    if indicator == "stochastic_rsi":
        rsi = _rsi(close, int(p.rsi_window))
        k = _stoch_from_series(rsi, int(p.stoch_window)).rolling(int(p.smooth_k), min_periods=int(p.smooth_k)).mean()
        d = k.rolling(int(p.smooth_d), min_periods=int(p.smooth_d)).mean()
        return _two_line_output(indicator, k, d, p, "stoch_rsi_k", "stoch_rsi_d", extra={"rsi": rsi})
    if indicator == "cci":
        typical = (high + low + close) / 3.0
        ma = typical.rolling(n, min_periods=_min_periods(p, n)).mean()
        md = typical.rolling(n, min_periods=_min_periods(p, n)).apply(lambda x: float(np.mean(np.abs(x - np.mean(x)))) if len(x) else np.nan, raw=True)
        cci = (typical - ma) / (float(p.cci_constant) * md.replace(0, np.nan))
        return _osc_output(indicator, cci, p)
    if indicator == "cmo":
        delta = close.diff()
        gain = delta.clip(lower=0.0).rolling(n, min_periods=_min_periods(p, n)).sum()
        loss = (-delta.clip(upper=0.0)).rolling(n, min_periods=_min_periods(p, n)).sum()
        cmo = 100.0 * (gain - loss) / (gain + loss).replace(0, np.nan)
        return _osc_output(indicator, cmo, p)
    if indicator == "momentum":
        return _zero_output(indicator, close - close.shift(n))
    if indicator == "roc":
        return _zero_output(indicator, 100.0 * (close / close.shift(n).replace(0, np.nan) - 1.0))
    if indicator == "rocp":
        return _zero_output(indicator, close / close.shift(n).replace(0, np.nan) - 1.0)
    if indicator == "rocr":
        return _ratio_output(indicator, close / close.shift(n).replace(0, np.nan))
    if indicator == "rocr100":
        return _ratio_output(indicator, 100.0 * close / close.shift(n).replace(0, np.nan), mid=100.0)
    if indicator == "williams_r":
        wr = -100.0 * (high.rolling(n, min_periods=n).max() - close) / (high.rolling(n, min_periods=n).max() - low.rolling(n, min_periods=n).min()).replace(0, np.nan)
        return _osc_output(indicator, wr, p)
    if indicator == "ultimate_oscillator":
        prev = close.shift(1)
        bp = close - pd.concat([low, prev], axis=1).min(axis=1)
        tr = pd.concat([high, prev], axis=1).max(axis=1) - pd.concat([low, prev], axis=1).min(axis=1)
        a1 = bp.rolling(int(p.short_window), min_periods=int(p.short_window)).sum() / tr.rolling(int(p.short_window), min_periods=int(p.short_window)).sum().replace(0, np.nan)
        a2 = bp.rolling(int(p.medium_window), min_periods=int(p.medium_window)).sum() / tr.rolling(int(p.medium_window), min_periods=int(p.medium_window)).sum().replace(0, np.nan)
        a3 = bp.rolling(int(p.long_window), min_periods=int(p.long_window)).sum() / tr.rolling(int(p.long_window), min_periods=int(p.long_window)).sum().replace(0, np.nan)
        uo = 100.0 * (4.0 * a1 + 2.0 * a2 + a3) / 7.0
        return _osc_output(indicator, uo, p)
    if indicator == "trix":
        e1 = _ema(close, n)
        e2 = _ema(e1, n)
        e3 = _ema(e2, n)
        return _zero_output(indicator, e3.pct_change() * 100.0)
    if indicator == "bop":
        return _zero_output(indicator, (close - open_) / (high - low).replace(0, np.nan))
    if indicator == "mfi":
        if volume is None:
            raise ValueError("MFI requires volume")
        typical = (high + low + close) / 3.0
        flow = typical * volume
        pos = pd.Series(np.where(typical.diff() > 0, flow, 0.0), index=close.index).rolling(n, min_periods=n).sum()
        neg = pd.Series(np.where(typical.diff() < 0, flow, 0.0), index=close.index).rolling(n, min_periods=n).sum()
        mfi = 100.0 - 100.0 / (1.0 + pos / neg.replace(0, np.nan))
        mfi[(neg == 0) & (pos > 0)] = 100.0
        mfi[(neg == 0) & (pos == 0)] = 50.0
        return _osc_output(indicator, mfi, p)
    if indicator == "awesome_oscillator":
        median = (high + low) / 2.0
        ao = median.rolling(int(p.fast_window), min_periods=int(p.fast_window)).mean() - median.rolling(int(p.slow_window), min_periods=int(p.slow_window)).mean()
        return _zero_output(indicator, ao)
    if indicator == "accelerator_oscillator":
        median = (high + low) / 2.0
        ao = median.rolling(int(p.fast_window), min_periods=int(p.fast_window)).mean() - median.rolling(int(p.slow_window), min_periods=int(p.slow_window)).mean()
        ac = ao - ao.rolling(int(p.signal_window), min_periods=int(p.signal_window)).mean()
        return _zero_output(indicator, ac, extra={"awesome_oscillator": ao})
    if indicator == "kst":
        return _kst(close, p)
    if indicator == "true_strength_index":
        return _tsi(close, p)
    if indicator == "connors_rsi":
        return _connors_rsi(close, p)
    if indicator == "relative_vigor_index":
        return _relative_vigor(open_, high, low, close, p)
    if indicator == "fisher_transform":
        return _fisher(high, low, p)
    if indicator == "stochastic_momentum_index":
        return _smi(high, low, close, p)
    if indicator == "kdj":
        return _kdj(high, low, close, p)
    if indicator == "demarker":
        demax = (high - high.shift(1)).clip(lower=0.0)
        demin = (low.shift(1) - low).clip(lower=0.0)
        dem = demax.rolling(n, min_periods=n).mean() / (demax.rolling(n, min_periods=n).mean() + demin.rolling(n, min_periods=n).mean()).replace(0, np.nan)
        return _osc_output(indicator, 100.0 * dem, p)
    if indicator == "elder_ray":
        basis = _ema(close, n)
        bull = high - basis
        bear = low - basis
        primary = bull + bear
        direction = "bullish" if (_last_float(bull) or 0.0) > 0 and (_last_float(bear) or 0.0) > 0 else "bearish" if (_last_float(bull) or 0.0) < 0 and (_last_float(bear) or 0.0) < 0 else "mixed"
        return _ComputeOutput(primary=primary, series={"value": primary, "bull_power": bull, "bear_power": bear, "ema": basis}, signal=direction, momentum_direction=direction, momentum_strength=_last_float(primary.abs()), zone="neutral")
    if indicator == "qstick":
        return _zero_output(indicator, (close - open_).rolling(n, min_periods=n).mean())
    if indicator == "coppock_curve":
        curve = _wma(_roc(close, int(p.long_window)) + _roc(close, int(p.short_window)), n)
        return _zero_output(indicator, curve)
    if indicator == "dpo":
        dpo = close - close.rolling(n, min_periods=n).mean().shift(n // 2 + 1)
        return _zero_output(indicator, dpo, diagnostics={"causal_variant": True})
    if indicator == "chande_forecast_oscillator":
        reg = _rolling_regression_value(close, n)
        cfo = 100.0 * (close - reg) / close.replace(0, np.nan)
        return _zero_output(indicator, cfo, extra={"regression": reg})
    if indicator == "relative_momentum_index":
        mom = close - close.shift(int(p.momentum_window))
        gain = mom.clip(lower=0.0)
        loss = -mom.clip(upper=0.0)
        avg_gain = _rma(gain, n)
        avg_loss = _rma(loss, n)
        rmi = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss.replace(0, np.nan))
        rmi[(avg_loss == 0) & (avg_gain > 0)] = 100.0
        rmi[(avg_loss == 0) & (avg_gain == 0)] = 50.0
        return _osc_output(indicator, rmi, p)
    raise ValueError(f"unsupported indicator {indicator}")


def _osc_output(indicator: str, value: pd.Series, p: MomentumParams, *, extra: Optional[Dict[str, pd.Series]] = None) -> _ComputeOutput:
    last = _last_float(value)
    ob = float(p.overbought)
    os = float(p.oversold)
    direction = _direction_from_level(last, ob, os) if last is not None else "unknown"
    sig = _zone(last, ob, os) if last is not None else "none"
    series = {"value": value}
    if extra:
        series.update(extra)
    return _ComputeOutput(primary=value, series=series, signal=sig, momentum_direction=direction, momentum_strength=_default_strength(last, ob, os), zone=sig, summary={"calculation": indicator})


def _zero_output(indicator: str, value: pd.Series, *, extra: Optional[Dict[str, pd.Series]] = None, diagnostics: Optional[Dict[str, Any]] = None) -> _ComputeOutput:
    last = _last_float(value)
    direction = "bullish" if last is not None and last > 0 else "bearish" if last is not None and last < 0 else "neutral"
    series = {"value": value}
    if extra:
        series.update(extra)
    return _ComputeOutput(primary=value, series=series, signal=direction, momentum_direction=direction, momentum_strength=abs(last) if last is not None else None, zone=direction, summary={"calculation": indicator}, diagnostics=dict(diagnostics or {}))


def _ratio_output(indicator: str, value: pd.Series, *, mid: float = 1.0) -> _ComputeOutput:
    last = _last_float(value)
    direction = "bullish" if last is not None and last > mid else "bearish" if last is not None and last < mid else "neutral"
    strength = abs(last - mid) if last is not None else None
    return _ComputeOutput(primary=value, series={"value": value}, signal=direction, momentum_direction=direction, momentum_strength=strength, zone=direction, summary={"calculation": indicator, "neutral_mid": mid})


def _two_line_output(indicator: str, line: pd.Series, signal_line: pd.Series, p: MomentumParams, line_name: str, signal_name: str, *, extra: Optional[Dict[str, pd.Series]] = None) -> _ComputeOutput:
    sig = _cross_signal(line, signal_line)
    last = _last_float(line)
    direction = _direction_from_level(last, float(p.overbought), float(p.oversold)) if last is not None else "unknown"
    series = {"value": line, line_name: line, signal_name: signal_line}
    if extra:
        series.update(extra)
    return _ComputeOutput(primary=line, series=series, signal=sig, momentum_direction=direction, momentum_strength=_default_strength(last, float(p.overbought), float(p.oversold)), zone=_zone(last, float(p.overbought), float(p.oversold)), summary={"calculation": indicator})


def _kst(close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    r1 = _roc(close, int(p.short_window)).rolling(int(p.smooth_window), min_periods=int(p.smooth_window)).mean()
    r2 = _roc(close, int(p.medium_window)).rolling(int(p.smooth_window), min_periods=int(p.smooth_window)).mean()
    r3 = _roc(close, int(p.long_window)).rolling(int(p.smooth_window), min_periods=int(p.smooth_window)).mean()
    r4_window = int(p.long_window) + int(p.smooth_window)
    r4 = _roc(close, r4_window).rolling(int(p.smooth_window), min_periods=int(p.smooth_window)).mean()
    kst = r1 + 2.0 * r2 + 3.0 * r3 + 4.0 * r4
    signal = kst.rolling(int(p.signal_window), min_periods=int(p.signal_window)).mean()
    return _two_line_output("kst", kst, signal, p, "kst", "signal", extra={"roc_short": r1, "roc_medium": r2, "roc_long": r3, "roc_extra": r4})


def _tsi(close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    pc = close.diff()
    double = _ema(_ema(pc, int(p.slow_window)), int(p.fast_window))
    abs_double = _ema(_ema(pc.abs(), int(p.slow_window)), int(p.fast_window))
    tsi = 100.0 * double / abs_double.replace(0, np.nan)
    signal = _ema(tsi, int(p.signal_window))
    return _two_line_output("true_strength_index", tsi, signal, p, "tsi", "signal")


def _connors_rsi(close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    rsi_price = _rsi(close, int(p.rsi_window))
    streak = _streak(close)
    rsi_streak = _rsi(streak, int(p.streak_rsi_window))
    roc = close.diff(int(p.roc_window))
    pr = roc.rolling(int(p.rank_window) + 1, min_periods=int(p.rank_window) + 1).apply(_percent_rank_last, raw=True)
    crsi = (rsi_price + rsi_streak + pr) / 3.0
    return _osc_output("connors_rsi", crsi, p, extra={"rsi_price": rsi_price, "rsi_streak": rsi_streak, "percent_rank": pr})


def _relative_vigor(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    den = (high - low).replace(0, np.nan)
    raw = (close - open_) / den
    rvi = raw.rolling(int(p.window), min_periods=int(p.window)).mean()
    signal = rvi.rolling(4, min_periods=4).mean()
    return _two_line_output("relative_vigor_index", rvi, signal, p, "rvi", "signal")


def _fisher(high: pd.Series, low: pd.Series, p: MomentumParams) -> _ComputeOutput:
    hl2 = (high + low) / 2.0
    highest = hl2.rolling(int(p.window), min_periods=int(p.window)).max()
    lowest = hl2.rolling(int(p.window), min_periods=int(p.window)).min()
    raw = 2.0 * ((hl2 - lowest) / (highest - lowest).replace(0, np.nan) - 0.5)
    raw = raw.clip(-0.999, 0.999)
    value = pd.Series(np.nan, index=hl2.index, dtype=float)
    fish = pd.Series(np.nan, index=hl2.index, dtype=float)
    for i, x in enumerate(raw):
        if pd.isna(x):
            continue
        prev_v = 0.0 if i == 0 or pd.isna(value.iloc[i - 1]) else value.iloc[i - 1]
        value.iloc[i] = float(np.clip(0.33 * x + 0.67 * prev_v, -0.999, 0.999))
        prev_f = 0.0 if i == 0 or pd.isna(fish.iloc[i - 1]) else fish.iloc[i - 1]
        fish.iloc[i] = 0.5 * math.log((1.0 + value.iloc[i]) / (1.0 - value.iloc[i])) + 0.5 * prev_f
    return _two_line_output("fisher_transform", fish, fish.shift(1), p, "fisher", "trigger")


def _smi(high: pd.Series, low: pd.Series, close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    hh = high.rolling(int(p.stoch_window), min_periods=int(p.stoch_window)).max()
    ll = low.rolling(int(p.stoch_window), min_periods=int(p.stoch_window)).min()
    mid = (hh + ll) / 2.0
    dist = close - mid
    rng = hh - ll
    smooth_dist = _ema(_ema(dist, int(p.smooth_k)), int(p.smooth_d))
    smooth_range = _ema(_ema(rng, int(p.smooth_k)), int(p.smooth_d))
    smi = 100.0 * smooth_dist / (0.5 * smooth_range).replace(0, np.nan)
    signal = _ema(smi, int(p.signal_window))
    return _two_line_output("stochastic_momentum_index", smi, signal, p, "smi", "signal")


def _kdj(high: pd.Series, low: pd.Series, close: pd.Series, p: MomentumParams) -> _ComputeOutput:
    rsv = _stoch_k(high, low, close, int(p.stoch_window))
    k = _recursive_smooth(rsv, int(p.smooth_k), start=50.0)
    d = _recursive_smooth(k, int(p.smooth_d), start=50.0)
    j = 3.0 * k - 2.0 * d
    return _two_line_output("kdj", j, d, p, "j", "d", extra={"k": k, "rsv": rsv})


def _rsi(series: pd.Series, n: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = _rma(gain, n)
    avg_loss = _rma(loss, n)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    out[(avg_loss == 0) & (avg_gain > 0)] = 100.0
    out[(avg_loss == 0) & (avg_gain == 0)] = 50.0
    return out


def _stoch_k(high: pd.Series, low: pd.Series, close: pd.Series, n: int) -> pd.Series:
    lowest = low.rolling(n, min_periods=n).min()
    highest = high.rolling(n, min_periods=n).max()
    den = highest - lowest
    out = 100.0 * (close - lowest) / den.replace(0, np.nan)
    out[(den == 0) & close.notna()] = 50.0
    return out


def _stoch_from_series(series: pd.Series, n: int) -> pd.Series:
    lowest = series.rolling(n, min_periods=n).min()
    highest = series.rolling(n, min_periods=n).max()
    den = highest - lowest
    out = 100.0 * (series - lowest) / den.replace(0, np.nan)
    out[(den == 0) & series.notna()] = 50.0
    return out


def _streak(close: pd.Series) -> pd.Series:
    out = pd.Series(0.0, index=close.index)
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i - 1]:
            out.iloc[i] = out.iloc[i - 1] + 1 if out.iloc[i - 1] > 0 else 1
        elif close.iloc[i] < close.iloc[i - 1]:
            out.iloc[i] = out.iloc[i - 1] - 1 if out.iloc[i - 1] < 0 else -1
        else:
            out.iloc[i] = 0.0
    return out


def _percent_rank_last(values: np.ndarray) -> float:
    if len(values) < 2 or np.isnan(values).any():
        return np.nan
    return 100.0 * float(np.sum(values[:-1] < values[-1])) / float(len(values) - 1)


def _rolling_regression_value(series: pd.Series, n: int) -> pd.Series:
    x = np.arange(n, dtype=float)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()

    def calc(y: np.ndarray) -> float:
        if np.isnan(y).any():
            return np.nan
        y_mean = y.mean()
        slope = float(((x - x_mean) * (y - y_mean)).sum() / x_var)
        intercept = float(y_mean - slope * x_mean)
        return intercept + slope * (n - 1)

    return series.rolling(n, min_periods=n).apply(calc, raw=True)


def _recursive_smooth(series: pd.Series, n: int, *, start: float) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    alpha = 1.0 / float(n)
    prev = float(start)
    for i, value in enumerate(series):
        if pd.isna(value):
            continue
        prev = alpha * float(value) + (1.0 - alpha) * prev
        out.iloc[i] = prev
    return out


def _roc(series: pd.Series, n: int) -> pd.Series:
    return 100.0 * (series / series.shift(n).replace(0, np.nan) - 1.0)


def _ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=int(n), adjust=False, min_periods=int(n)).mean()


def _rma(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(alpha=1.0 / int(n), adjust=False, min_periods=int(n)).mean()


def _wma(series: pd.Series, n: int) -> pd.Series:
    weights = np.arange(1, int(n) + 1, dtype=float)
    return series.rolling(int(n), min_periods=int(n)).apply(lambda x: float(np.dot(x, weights) / weights.sum()) if len(x) == len(weights) else np.nan, raw=True)


def _min_periods(p: MomentumParams, n: int) -> int:
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


def _zone(value: Optional[float], overbought: float, oversold: float) -> str:
    if value is None:
        return "unknown"
    if overbought == oversold:
        if value > overbought:
            return "overbought"
        if value < oversold:
            return "oversold"
        return "neutral"
    if value >= overbought:
        return "overbought"
    if value <= oversold:
        return "oversold"
    return "neutral"


def _direction_from_level(value: Optional[float], overbought: float, oversold: float) -> str:
    if value is None:
        return "unknown"
    midpoint = (overbought + oversold) / 2.0
    if value > midpoint:
        return "bullish"
    if value < midpoint:
        return "bearish"
    return "neutral"


def _default_strength(value: Optional[float], overbought: float, oversold: float) -> Optional[float]:
    if value is None:
        return None
    midpoint = (overbought + oversold) / 2.0
    scale = abs(overbought - oversold) / 2.0
    if scale == 0:
        scale = max(abs(midpoint), 1.0)
    return abs(value - midpoint) / scale


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
    "MomentumParams",
    "MomentumReport",
    "normalize_momentum_input",
    "run_momentum_indicator",
]
