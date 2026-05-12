"""
quant_strategy_tokenizer.indicators.volatility_common
=====================================================
Purpose: shared implementation layer for atomic volatility indicator tokens.
Core idea: Normalize caller-supplied price/OHLC data, calculate range,
return, band, squeeze, and volatility-regime measures with explicit parameter
and backend handling, then return a uniform VolatilityReport. Assumes
volatility tokens should describe dispersion, expansion/contraction, and risk
regime without owning data sourcing or execution.
Inputs: raw user data, DataFrameSpec/ExtractorSpec, VolatilityParams-compatible
configuration, indicator name, input kind, and ModuleRunContext.
Outputs: VolatilityReport wrapped in ModuleResult with last values, volatility
direction, level, regime, optional series, diagnostics, warnings, and report
files when requested.
Failure semantics: invalid params, missing fields, insufficient history,
unsupported backend, unavailable TA-Lib, zero denominators that prevent a valid
output, and calculation errors return ModuleResult.fail.
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
class VolatilityParams:
    """Generic volatility-indicator options used by atomic wrapper modules.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`. Native uses pandas/numpy. Talib
      requires TA-Lib and fails explicitly if unavailable. Auto uses TA-Lib
      only for supported functions when installed.
    - `value_field`, `volume_field`: logical fields resolved through
      DataFrameSpec. Most volatility modules use close as the value field.
    - window fields: lookbacks in rows/bars. Unused fields are ignored by each
      indicator but kept for a stable interface.
    - `annualize`, `periods_per_year`: controls annualized return-volatility
      outputs. Set `annualize=False` to keep per-bar units.
    - `low_percentile`, `high_percentile`, `extreme_percentile`: volatility
      regime thresholds used only for report semantics.
    """

    backend: str = "native"
    value_field: str = "close"
    volume_field: str = "volume"
    window: int = 20
    min_periods: Optional[int] = None
    fast_window: int = 10
    slow_window: int = 20
    signal_window: int = 9
    atr_window: int = 14
    annualize: bool = True
    periods_per_year: float = 252.0
    multiplier: float = 2.0
    stddev_multiplier: float = 2.0
    regime_window: int = 100
    low_percentile: float = 25.0
    high_percentile: float = 75.0
    extreme_percentile: float = 90.0
    smoothing: str = "sma"
    ewma_lambda: float = 0.94
    ddof: int = 1


@dataclass
class VolatilityReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    volatility_direction: str = "unknown"
    volatility_level: str = "unknown"
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
    volatility_direction: str = "unknown"
    volatility_level: str = "unknown"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_volatility_input(request: Any, input_kind: str) -> ModuleResult[Any]:
    params = request.params
    value_field = str(getattr(params, "value_field", "close") or "close")
    if input_kind == "price":
        required = [value_field]
    elif input_kind == "ohlc":
        required = ["high", "low", "close"]
    elif input_kind == "ohlc_open":
        required = ["open", "high", "low", "close"]
    else:
        required = [value_field]
    return normalize_frame(request.data, required_fields=required, optional_fields=[], spec=request.spec, extractor=request.extractor)


def run_volatility_indicator(indicator: str, request: Any, *, input_kind: str, module_name: str) -> ModuleResult[VolatilityReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error

    backend_result = _resolve_backend(str(getattr(params, "backend", "native") or "native"), indicator)
    if not backend_result.ok:
        return ModuleResult.fail(backend_result.failure.kind, backend_result.failure.message, details=backend_result.failure.details)
    backend, talib_mod = backend_result.value

    norm = normalize_volatility_input(request, input_kind)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")

    frame = nf.frame
    used = dict(nf.used_fields)
    value_key = str(getattr(params, "value_field", "close") or "close")
    close_col = used.get(value_key) or used.get("close")
    if close_col is None:
        return ModuleResult.fail("missing_required_field", "volatility indicator needs a resolved price field")
    close = pd.to_numeric(frame[close_col], errors="coerce")
    open_ = pd.to_numeric(frame[used["open"]], errors="coerce") if "open" in used else close
    high = pd.to_numeric(frame[used["high"]], errors="coerce") if "high" in used else close
    low = pd.to_numeric(frame[used["low"]], errors="coerce") if "low" in used else close

    min_rows = _minimum_rows(indicator, params)
    numeric_rows = int(close.dropna().shape[0])
    if numeric_rows < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} numeric rows, got {numeric_rows}")

    try:
        if backend == "talib":
            computed = _compute_talib(indicator, params, open_, high, low, close, talib_mod)
        else:
            computed = _compute_native(indicator, params, open_, high, low, close)
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
    level = computed.volatility_level if computed.volatility_level != "unknown" else classify_volatility_level(
        normalized,
        low=float(params.low_percentile),
        high=float(params.high_percentile),
        extreme=float(params.extreme_percentile),
    )
    direction = computed.volatility_direction
    if direction == "unknown":
        direction = classify_volatility_direction(primary)
    regime = computed.regime if computed.regime != "unknown" else level
    signal = computed.signal if computed.signal != "none" else _signal_from_level_direction(level, direction)

    detail = request.context.detail_level
    include_series = detail_at_least(detail, DetailLevel.FULL)
    report = VolatilityReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        volatility_direction=direction,
        volatility_level=level,
        signal=signal,
        regime=regime,
        normalized_value=normalized,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={
            "rows": int(len(close)),
            "backend": backend,
            "input_kind": input_kind,
            "annualized": bool(params.annualize),
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
        },
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "level": level, "direction": direction})],
        warnings=nf.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def classify_volatility_direction(series: pd.Series, *, tolerance: float = 0.01) -> str:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 2:
        return "unknown"
    prev = float(valid.iloc[-2])
    curr = float(valid.iloc[-1])
    if not math.isfinite(prev) or not math.isfinite(curr):
        return "unknown"
    scale = max(abs(prev), 1e-12)
    if curr > prev + scale * tolerance:
        return "expanding"
    if curr < prev - scale * tolerance:
        return "contracting"
    return "stable"


def classify_volatility_level(normalized_value: Optional[float], *, low: float = 25.0, high: float = 75.0, extreme: float = 90.0) -> str:
    if normalized_value is None or not math.isfinite(float(normalized_value)):
        return "unknown"
    value = float(normalized_value)
    if value <= float(low):
        return "low"
    if value <= float(high):
        return "normal"
    if value <= float(extreme):
        return "high"
    return "extreme"


def last_percentile(series: pd.Series, window: int) -> Optional[float]:
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < max(5, min(int(window), 20)):
        return None
    tail = valid.tail(max(1, int(window)))
    last = float(tail.iloc[-1])
    rank = float((tail <= last).sum()) / float(len(tail))
    return 100.0 * rank


def _validate_params(params: VolatilityParams) -> Optional[ModuleResult[Any]]:
    backend = str(getattr(params, "backend", "native") or "native").lower()
    if backend not in {"native", "talib", "auto"}:
        return ModuleResult.fail("invalid_parameter", "backend must be native, talib, or auto", field="backend")
    for name in ("window", "fast_window", "slow_window", "signal_window", "atr_window", "regime_window"):
        try:
            value = int(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    for name in ("periods_per_year", "multiplier", "stddev_multiplier"):
        try:
            value = float(getattr(params, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be numeric", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    try:
        lam = float(getattr(params, "ewma_lambda"))
    except Exception:
        return ModuleResult.fail("invalid_parameter", "ewma_lambda must be numeric", field="ewma_lambda")
    if not (0.0 < lam < 1.0):
        return ModuleResult.fail("invalid_parameter", "ewma_lambda must satisfy 0 < value < 1", field="ewma_lambda")
    try:
        ddof = int(getattr(params, "ddof"))
    except Exception:
        return ModuleResult.fail("invalid_parameter", "ddof must be an integer", field="ddof")
    if ddof < 0:
        return ModuleResult.fail("invalid_parameter", "ddof must be non-negative", field="ddof")
    low = float(getattr(params, "low_percentile"))
    high = float(getattr(params, "high_percentile"))
    extreme = float(getattr(params, "extreme_percentile"))
    if not (0.0 <= low < high < extreme <= 100.0):
        return ModuleResult.fail("invalid_parameter", "percentile thresholds must satisfy 0 <= low < high < extreme <= 100", field="low_percentile")
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
    "true_range",
    "natr",
    "bollinger_bands",
    "bollinger_bandwidth",
    "percent_b",
}


def _minimum_rows(indicator: str, p: VolatilityParams) -> int:
    n = int(p.window)
    if indicator in {"natr"}:
        return n + 1
    if indicator in {"gap_range", "true_range"}:
        return 2
    if indicator in {"chaikin_volatility"}:
        return int(p.fast_window) + int(p.slow_window) + 2
    if indicator in {"mass_index"}:
        return max(n, int(p.fast_window) * 2) + 2
    if indicator in {"volatility_ratio"}:
        return int(p.long_window if hasattr(p, "long_window") else p.slow_window) + 2
    if indicator in {"volatility_of_volatility"}:
        return n + int(p.signal_window) + 2
    if indicator in {"yang_zhang_volatility"}:
        return n + 2
    if indicator in {"ttm_squeeze", "bollinger_keltner_squeeze"}:
        return max(n, int(p.atr_window)) + 2
    return max(n + 1, int(getattr(p, "min_periods", 0) or 0), 2)


def _compute_talib(indicator: str, p: VolatilityParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, talib: Any) -> _ComputeOutput:
    o = open_.astype(float).to_numpy()
    h = high.astype(float).to_numpy()
    l = low.astype(float).to_numpy()
    c = close.astype(float).to_numpy()
    n = int(p.window)
    if indicator == "true_range":
        tr = _series(talib.TRANGE(h, l, c), close.index)
        return _vol_output(indicator, tr, {"value": tr}, calculation="talib.TRANGE")
    if indicator == "natr":
        natr = _series(talib.NATR(h, l, c, timeperiod=n), close.index)
        return _vol_output(indicator, natr, {"value": natr}, calculation="talib.NATR")
    if indicator in {"bollinger_bands", "bollinger_bandwidth", "percent_b"}:
        upper, middle, lower = talib.BBANDS(
            c,
            timeperiod=n,
            nbdevup=float(p.stddev_multiplier),
            nbdevdn=float(p.stddev_multiplier),
            matype=0,
        )
        return _bb_output(indicator, close, _series(middle, close.index), _series(upper, close.index), _series(lower, close.index), calculation="talib.BBANDS")
    raise ValueError(f"unsupported talib indicator {indicator}; open length={len(o)}")


def _compute_native(indicator: str, p: VolatilityParams, open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> _ComputeOutput:
    n = int(p.window)
    tr = _true_range(high, low, close)
    price_range = (high - low).abs()
    log_ret = _log_return(close)
    if indicator == "true_range":
        return _vol_output(indicator, tr, {"value": tr, "high_low": price_range}, calculation="true_range")
    if indicator == "natr":
        atr = _rma(tr, n, min_periods=_min_periods(p, n))
        natr = 100.0 * atr / close.abs().replace(0, np.nan)
        return _vol_output(indicator, natr, {"value": natr, "atr": atr, "true_range": tr}, calculation="100*ATR/close")
    if indicator == "high_low_range":
        return _vol_output(indicator, price_range, {"value": price_range}, calculation="high-low")
    if indicator == "rolling_range":
        rolling = high.rolling(n, min_periods=_min_periods(p, n)).max() - low.rolling(n, min_periods=_min_periods(p, n)).min()
        return _vol_output(indicator, rolling, {"value": rolling}, calculation="rolling_high-rolling_low")
    if indicator == "average_range":
        avg = price_range.rolling(n, min_periods=_min_periods(p, n)).mean()
        return _vol_output(indicator, avg, {"value": avg, "range": price_range}, calculation="rolling_mean(high-low)")
    if indicator == "gap_range":
        gap = (open_ - close.shift(1)).abs()
        return _vol_output(indicator, gap, {"value": gap}, calculation="abs(open-prior_close)")
    if indicator == "range_percent":
        rp = 100.0 * price_range / close.abs().replace(0, np.nan)
        return _vol_output(indicator, rp, {"value": rp, "range": price_range}, calculation="100*(high-low)/close")
    if indicator == "range_expansion":
        baseline = price_range.rolling(n, min_periods=_min_periods(p, n)).mean().shift(1)
        ratio = price_range / baseline.replace(0, np.nan)
        return _vol_output(indicator, ratio, {"value": ratio, "range": price_range, "baseline": baseline}, calculation="range/prior_average_range")
    if indicator == "rolling_stddev":
        s = log_ret.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof))
        return _vol_output(indicator, s, {"value": s, "log_return": log_ret}, calculation="rolling_std(log_return)")
    if indicator == "rolling_variance":
        var = log_ret.rolling(n, min_periods=_min_periods(p, n)).var(ddof=int(p.ddof))
        return _vol_output(indicator, var, {"value": var, "log_return": log_ret}, calculation="rolling_var(log_return)")
    if indicator == "historical_volatility":
        hv = _annualize(log_ret.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof)), p)
        return _vol_output(indicator, hv, {"value": hv, "log_return": log_ret}, calculation="annualized_rolling_std(log_return)")
    if indicator == "realized_volatility":
        rv = (log_ret.pow(2).rolling(n, min_periods=_min_periods(p, n)).sum() * _annual_factor(p) / float(n)).pow(0.5)
        if not bool(p.annualize):
            rv = log_ret.pow(2).rolling(n, min_periods=_min_periods(p, n)).sum().pow(0.5)
        return _vol_output(indicator, rv, {"value": rv, "log_return": log_ret}, calculation="sqrt(sum(log_return^2))")
    if indicator == "ewma_volatility":
        alpha = 1.0 - float(p.ewma_lambda)
        ewv = log_ret.pow(2).ewm(alpha=alpha, adjust=False, min_periods=_min_periods(p, n)).mean().pow(0.5)
        return _vol_output(indicator, _annualize(ewv, p), {"value": _annualize(ewv, p), "log_return": log_ret}, calculation="ewma_sqrt_return_variance")
    if indicator == "parkinson_volatility":
        term = (np.log((high / low.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))).pow(2) / (4.0 * math.log(2.0))
        vol = _annualize(term.rolling(n, min_periods=_min_periods(p, n)).mean().pow(0.5), p)
        return _vol_output(indicator, vol, {"value": vol, "range_term": term}, calculation="Parkinson high-low estimator")
    if indicator == "garman_klass_volatility":
        hl = np.log((high / low.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        co = np.log((close / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        term = 0.5 * hl.pow(2) - (2.0 * math.log(2.0) - 1.0) * co.pow(2)
        vol = _annualize(term.clip(lower=0.0).rolling(n, min_periods=_min_periods(p, n)).mean().pow(0.5), p)
        return _vol_output(indicator, vol, {"value": vol, "gk_term": term}, calculation="Garman-Klass estimator")
    if indicator == "rogers_satchell_volatility":
        hc = np.log((high / close.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        ho = np.log((high / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        lc = np.log((low / close.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        lo = np.log((low / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
        term = hc * ho + lc * lo
        vol = _annualize(term.clip(lower=0.0).rolling(n, min_periods=_min_periods(p, n)).mean().pow(0.5), p)
        return _vol_output(indicator, vol, {"value": vol, "rs_term": term}, calculation="Rogers-Satchell estimator")
    if indicator == "yang_zhang_volatility":
        return _yang_zhang(open_, high, low, close, p)
    if indicator == "downside_volatility":
        downside = log_ret.clip(upper=0.0)
        vol = _annualize(downside.pow(2).rolling(n, min_periods=_min_periods(p, n)).mean().pow(0.5), p)
        return _vol_output(indicator, vol, {"value": vol, "downside_return": downside}, calculation="sqrt(mean(negative_return^2))")
    if indicator == "volatility_of_volatility":
        base = _annualize(log_ret.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof)), p)
        vov = base.rolling(int(p.signal_window), min_periods=int(p.signal_window)).std(ddof=int(p.ddof))
        return _vol_output(indicator, vov, {"value": vov, "base_volatility": base}, calculation="rolling_std(historical_volatility)")
    if indicator in {"bollinger_bands", "bollinger_bandwidth", "percent_b"}:
        mid = close.rolling(n, min_periods=_min_periods(p, n)).mean()
        std = close.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof))
        return _bb_output(indicator, close, mid, mid + float(p.stddev_multiplier) * std, mid - float(p.stddev_multiplier) * std, calculation="native Bollinger bands")
    if indicator in {"zscore", "zscore_bands"}:
        mid = close.rolling(n, min_periods=_min_periods(p, n)).mean()
        std = close.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof))
        z = (close - mid) / std.replace(0, np.nan)
        if indicator == "zscore_bands":
            upper = mid + float(p.stddev_multiplier) * std
            lower = mid - float(p.stddev_multiplier) * std
            return _z_output(indicator, z, {"value": z, "middle": mid, "upper": upper, "lower": lower, "stddev": std})
        return _z_output(indicator, z, {"value": z, "middle": mid, "stddev": std})
    if indicator == "ttm_squeeze":
        return _squeeze_output(indicator, high, low, close, p, ratio_mode=False)
    if indicator == "bollinger_keltner_squeeze":
        return _squeeze_output(indicator, high, low, close, p, ratio_mode=True)
    if indicator == "chaikin_volatility":
        ema_range = price_range.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        shifted = ema_range.shift(int(p.slow_window))
        cv = 100.0 * (ema_range - shifted) / shifted.replace(0, np.nan)
        direction = "expanding" if (_last_float(cv) or 0.0) > 0 else "contracting" if (_last_float(cv) or 0.0) < 0 else "stable"
        return _vol_output(indicator, cv, {"value": cv, "ema_range": ema_range}, direction=direction, calculation="100*ROC(EMA(high-low))")
    if indicator == "mass_index":
        ema1 = price_range.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        ema2 = ema1.ewm(span=int(p.fast_window), adjust=False, min_periods=int(p.fast_window)).mean()
        ratio = ema1 / ema2.replace(0, np.nan)
        mi = ratio.rolling(n, min_periods=_min_periods(p, n)).sum()
        signal = "reversal_risk" if (_last_float(mi) or 0.0) >= 27.0 else "normal"
        return _vol_output(indicator, mi, {"value": mi, "ema_ratio": ratio}, signal=signal, calculation="sum(EMA(range)/EMA(EMA(range)))")
    if indicator == "ulcer_index":
        peak = close.rolling(n, min_periods=_min_periods(p, n)).max()
        drawdown = 100.0 * (close - peak) / peak.replace(0, np.nan)
        ui = drawdown.pow(2).rolling(n, min_periods=_min_periods(p, n)).mean().pow(0.5)
        return _vol_output(indicator, ui, {"value": ui, "drawdown_pct": drawdown}, calculation="sqrt(mean(drawdown_pct^2))")
    if indicator in {"relative_volatility_index", "inertia"}:
        return _relative_volatility_output(indicator, close, p)
    if indicator == "vertical_horizontal_filter":
        numerator = (close - close.shift(n)).abs()
        denominator = close.diff().abs().rolling(n, min_periods=_min_periods(p, n)).sum()
        vhf = numerator / denominator.replace(0, np.nan)
        direction = "contracting" if (_last_float(vhf) or 0.0) < 0.2 else "expanding" if (_last_float(vhf) or 0.0) > 0.5 else "stable"
        return _vol_output(indicator, vhf, {"value": vhf}, direction=direction, calculation="abs(net_change)/sum(abs(change))")
    if indicator == "volatility_ratio":
        short = _annualize(log_ret.rolling(int(p.fast_window), min_periods=int(p.fast_window)).std(ddof=int(p.ddof)), p)
        long = _annualize(log_ret.rolling(int(p.slow_window), min_periods=int(p.slow_window)).std(ddof=int(p.ddof)), p)
        ratio = short / long.replace(0, np.nan)
        direction = "expanding" if (_last_float(ratio) or 0.0) > 1.0 else "contracting" if (_last_float(ratio) or 0.0) < 1.0 else "stable"
        return _vol_output(indicator, ratio, {"value": ratio, "short_volatility": short, "long_volatility": long}, direction=direction, calculation="short_volatility/long_volatility")
    if indicator == "volatility_regime":
        hv = _annualize(log_ret.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof)), p)
        pct = _rolling_percentile_series(hv, int(p.regime_window))
        level = classify_volatility_level(_last_float(pct), low=float(p.low_percentile), high=float(p.high_percentile), extreme=float(p.extreme_percentile))
        return _ComputeOutput(
            primary=pct,
            series={"value": pct, "base_volatility": hv},
            signal=level,
            volatility_level=level,
            regime=level,
            normalized_value=_last_float(pct),
            summary={"calculation": "rolling_percentile(historical_volatility)"},
        )
    raise ValueError(f"unsupported indicator {indicator}")


def _vol_output(
    indicator: str,
    primary: pd.Series,
    series: Dict[str, pd.Series],
    *,
    signal: str = "none",
    direction: str = "unknown",
    calculation: str = "",
    diagnostics: Optional[Dict[str, Any]] = None,
) -> _ComputeOutput:
    return _ComputeOutput(
        primary=primary,
        series=series,
        signal=signal,
        volatility_direction=direction,
        summary={"calculation": calculation or indicator},
        diagnostics=dict(diagnostics or {}),
    )


def _bb_output(indicator: str, close: pd.Series, middle: pd.Series, upper: pd.Series, lower: pd.Series, *, calculation: str) -> _ComputeOutput:
    width_abs = (upper - lower).abs()
    bandwidth = 100.0 * width_abs / middle.abs().replace(0, np.nan)
    percent_b = (close - lower) / width_abs.replace(0, np.nan)
    if indicator == "percent_b":
        primary = percent_b
    else:
        primary = bandwidth
    signal = "squeeze" if (_last_float(bandwidth) or 0.0) <= 5.0 else "expanded" if (_last_float(bandwidth) or 0.0) >= 20.0 else "normal"
    return _ComputeOutput(
        primary=primary,
        series={"value": primary, "middle": middle, "upper": upper, "lower": lower, "bandwidth": bandwidth, "percent_b": percent_b},
        signal=signal,
        volatility_direction=classify_volatility_direction(bandwidth),
        summary={"calculation": calculation},
    )


def _z_output(indicator: str, z: pd.Series, series: Dict[str, pd.Series]) -> _ComputeOutput:
    last = _last_float(z)
    signal = "high_positive_deviation" if last is not None and last >= 2.0 else "high_negative_deviation" if last is not None and last <= -2.0 else "normal"
    return _ComputeOutput(
        primary=z,
        series=series,
        signal=signal,
        volatility_direction=classify_volatility_direction(z.abs()),
        normalized_value=None if last is None else min(100.0, abs(last) * 25.0),
        summary={"calculation": "rolling z-score"},
    )


def _squeeze_output(indicator: str, high: pd.Series, low: pd.Series, close: pd.Series, p: VolatilityParams, *, ratio_mode: bool) -> _ComputeOutput:
    n = int(p.window)
    mid = close.rolling(n, min_periods=_min_periods(p, n)).mean()
    std = close.rolling(n, min_periods=_min_periods(p, n)).std(ddof=int(p.ddof))
    bb_upper = mid + float(p.stddev_multiplier) * std
    bb_lower = mid - float(p.stddev_multiplier) * std
    ema_mid = close.ewm(span=n, adjust=False, min_periods=_min_periods(p, n)).mean()
    atr = _rma(_true_range(high, low, close), int(p.atr_window), min_periods=int(p.atr_window))
    kc_upper = ema_mid + float(p.multiplier) * atr
    kc_lower = ema_mid - float(p.multiplier) * atr
    bb_width = (bb_upper - bb_lower).abs()
    kc_width = (kc_upper - kc_lower).abs()
    ratio = bb_width / kc_width.replace(0, np.nan)
    squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
    primary = ratio if ratio_mode else squeeze_on.astype(float)
    valid = squeeze_on.dropna()
    if len(valid) >= 2 and bool(valid.iloc[-2]) and not bool(valid.iloc[-1]):
        signal = "squeeze_release"
    elif len(valid) >= 1 and bool(valid.iloc[-1]):
        signal = "squeeze_on"
    else:
        signal = "squeeze_off"
    direction = "contracting" if signal == "squeeze_on" else "expanding" if signal == "squeeze_release" else classify_volatility_direction(ratio)
    return _ComputeOutput(
        primary=primary,
        series={
            "value": primary,
            "ratio": ratio,
            "squeeze_on": squeeze_on.astype(float),
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "kc_upper": kc_upper,
            "kc_lower": kc_lower,
        },
        signal=signal,
        volatility_direction=direction,
        summary={"calculation": "Bollinger bands inside Keltner channel"},
    )


def _relative_volatility_output(indicator: str, close: pd.Series, p: VolatilityParams) -> _ComputeOutput:
    n = int(p.fast_window)
    vol = close.diff().rolling(n, min_periods=n).std(ddof=int(p.ddof))
    up = vol.where(close.diff() > 0.0, 0.0)
    down = vol.where(close.diff() < 0.0, 0.0)
    up_avg = _rma(up, n, min_periods=n)
    down_avg = _rma(down, n, min_periods=n)
    rvi = 100.0 * up_avg / (up_avg + down_avg).replace(0, np.nan)
    if indicator == "inertia":
        value = _rolling_regression_endpoint(rvi, int(p.window))
        signal = "bullish_volatility_bias" if (_last_float(value) or 0.0) > 50.0 else "bearish_volatility_bias"
        return _ComputeOutput(primary=value, series={"value": value, "relative_volatility_index": rvi}, signal=signal, summary={"calculation": "linear_regression(relative_volatility_index)"})
    signal = "bullish_volatility_bias" if (_last_float(rvi) or 0.0) > 50.0 else "bearish_volatility_bias"
    return _ComputeOutput(primary=rvi, series={"value": rvi}, signal=signal, summary={"calculation": "RSI-style up/down volatility ratio"})


def _yang_zhang(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, p: VolatilityParams) -> _ComputeOutput:
    n = int(p.window)
    overnight = np.log((open_ / close.shift(1).replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    close_open = np.log((close / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    hc = np.log((high / close.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    ho = np.log((high / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    lc = np.log((low / close.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    lo = np.log((low / open_.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan))
    rs = hc * ho + lc * lo
    k = 0.34 / (1.34 + (n + 1.0) / max(n - 1.0, 1.0))
    overnight_var = overnight.rolling(n, min_periods=_min_periods(p, n)).var(ddof=int(p.ddof))
    close_open_var = close_open.rolling(n, min_periods=_min_periods(p, n)).var(ddof=int(p.ddof))
    rs_mean = rs.clip(lower=0.0).rolling(n, min_periods=_min_periods(p, n)).mean()
    yz = (overnight_var + k * close_open_var + (1.0 - k) * rs_mean).clip(lower=0.0).pow(0.5)
    yz = _annualize(yz, p)
    return _vol_output(
        "yang_zhang_volatility",
        yz,
        {"value": yz, "overnight_variance": overnight_var, "open_close_variance": close_open_var, "rogers_satchell": rs_mean},
        calculation="Yang-Zhang estimator",
    )


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev = close.shift(1)
    return pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)


def _log_return(close: pd.Series) -> pd.Series:
    ratio = close / close.shift(1).replace(0, np.nan)
    return np.log(ratio.replace([np.inf, -np.inf], np.nan))


def _annualize(series: pd.Series, p: VolatilityParams) -> pd.Series:
    if not bool(p.annualize):
        return series
    return series * math.sqrt(float(p.periods_per_year))


def _annual_factor(p: VolatilityParams) -> float:
    return float(p.periods_per_year) if bool(p.annualize) else 1.0


def _rma(series: pd.Series, n: int, *, min_periods: Optional[int] = None) -> pd.Series:
    return series.ewm(alpha=1.0 / int(n), adjust=False, min_periods=int(min_periods if min_periods is not None else n)).mean()


def _rolling_regression_endpoint(series: pd.Series, n: int) -> pd.Series:
    x = np.arange(int(n), dtype=float)
    x_mean = float(x.mean())
    x_var = float(((x - x_mean) ** 2).sum())

    def calc(y: np.ndarray) -> float:
        if np.isnan(y).any():
            return np.nan
        y_mean = float(y.mean())
        slope = float(((x - x_mean) * (y - y_mean)).sum() / x_var)
        intercept = y_mean - slope * x_mean
        return float(intercept + slope * (n - 1))

    return series.rolling(int(n), min_periods=int(n)).apply(calc, raw=True)


def _rolling_percentile_series(series: pd.Series, n: int) -> pd.Series:
    def calc(values: np.ndarray) -> float:
        vals = values[~np.isnan(values)]
        if len(vals) == 0:
            return np.nan
        last = vals[-1]
        return 100.0 * float((vals <= last).sum()) / float(len(vals))

    return series.rolling(int(n), min_periods=max(5, min(int(n), 20))).apply(calc, raw=True)


def _signal_from_level_direction(level: str, direction: str) -> str:
    if level in {"high", "extreme"} and direction == "expanding":
        return "risk_expanding"
    if level == "low" and direction == "contracting":
        return "compression"
    if direction in {"expanding", "contracting", "stable"}:
        return direction
    return "none"


def _min_periods(p: VolatilityParams, n: int) -> int:
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
    "VolatilityParams",
    "VolatilityReport",
    "normalize_volatility_input",
    "run_volatility_indicator",
    "classify_volatility_direction",
    "classify_volatility_level",
    "last_percentile",
]
