"""
quant_strategy_tokenizer.indicators.vwap
========================================
Purpose: calculate rolling VWAP and touch/cross diagnostics from price and volume data.
Core idea: Select a price source, compute rolling price-volume over volume, then classify price interaction with VWAP by cross or tolerance band. Assumes volume-weighted price is a useful intraperiod reference and touch semantics must be explicit.
Inputs: OHLCV-like data, DataFrameSpec mapping, VWAPParams, optional ExtractorSpec, and ModuleRunContext.
Outputs: VWAPReport with latest VWAP, latest price, deviation, touch/cross counts, optional series, and diagnostics.
Failure semantics: missing price/volume fields, invalid window, zero volume, insufficient rows, or bad normalization return ModuleResult.fail.
Market generalization: works for any market with caller-provided price and volume fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class VWAPParams:
    """VWAP calculation and touch-diagnostic options.

    Configuration:
    - `window`: rolling VWAP lookback in rows/bars.
    - `price_source`: price construction; choose `typical`, `hlc3`, `ohlc4`,
      `close`, or `price` depending on supplied data.
    - `touch_band`: optional absolute proximity band around VWAP. Default zero
      counts VWAP touches as price/VWAP crossovers only. Positive values count
      either a crossover or proximity within the band.
    """

    window: int = 48
    price_source: str = "typical"  # close|price|typical|hlc3|ohlc4
    touch_band: float = 0.0


@dataclass
class VWAPRequest:
    data: Any
    params: VWAPParams = field(default_factory=VWAPParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="vwap"))


@dataclass
class VWAPReport:
    quality: str
    window: int
    last_value: Optional[float]
    last_price: Optional[float]
    last_deviation: Optional[float]
    touch_count: int = 0
    cross_count: int = 0
    no_touch_run: int = 0
    series: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: VWAPRequest):
    src = str(request.params.price_source).lower()
    required = ["volume"]
    if src in ("typical", "hlc3"):
        required += ["high", "low", "close"]
    elif src == "ohlc4":
        required += ["open", "high", "low", "close"]
    elif src == "price":
        required += ["price"]
    else:
        required += ["close"]
    return normalize_frame(request.data, required_fields=required, spec=request.spec, extractor=request.extractor)


def run(request: VWAPRequest) -> ModuleResult[VWAPReport]:
    params = request.params
    n = int(params.window)
    if n <= 0:
        return ModuleResult.fail("invalid_parameter", "VWAP window must be positive", field="window")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    price = _price_series(nf.frame, nf.used_fields, str(params.price_source).lower())
    volume = nf.frame[nf.used_fields["volume"]]
    valid = pd.DataFrame({"price": price, "volume": volume}).dropna()
    if len(valid) < n:
        return ModuleResult.fail("insufficient_data", f"need at least {n} price/volume rows, got {len(valid)}")
    if (valid["volume"] <= 0).all():
        return ModuleResult.fail("invalid_volume", "volume/proxy-volume field contains no positive values", field=nf.used_fields["volume"])
    pv = valid["price"] * valid["volume"]
    denom = valid["volume"].rolling(n, min_periods=n).sum()
    vwap = pv.rolling(n, min_periods=n).sum() / denom.replace(0, pd.NA)
    last_value = None if vwap.empty or pd.isna(vwap.iloc[-1]) else float(vwap.iloc[-1])
    last_price = None if valid.empty or pd.isna(valid["price"].iloc[-1]) else float(valid["price"].iloc[-1])
    dev = None if last_value is None or last_price is None or last_value == 0 else float((last_price - last_value) / last_value)
    band = float(params.touch_band or 0.0)
    if band < 0:
        return ModuleResult.fail("invalid_parameter", "touch_band must be non-negative", field="touch_band")
    spread = valid["price"] - vwap
    usable = vwap.notna() & spread.notna()
    crosses = _crosses_zero(spread) & usable
    if band > 0:
        band_touches = (spread.abs() <= band) & usable
        touches = (crosses | band_touches).fillna(False)
        touch_mode = "cross_or_band"
    else:
        band_touches = pd.Series(False, index=spread.index)
        touches = crosses.fillna(False)
        touch_mode = "cross"
    no_touch_run = 0
    for flag in reversed(touches[usable].tolist()):
        if flag:
            break
        no_touch_run += 1
    detail = request.context.detail_level
    report = VWAPReport(
        quality="ok" if last_value is not None else "insufficient_data",
        window=n,
        last_value=last_value,
        last_price=last_price,
        last_deviation=dev,
        touch_count=int(touches.sum()),
        cross_count=int(crosses.sum()),
        no_touch_run=int(no_touch_run),
        series=[None if pd.isna(x) else float(x) for x in vwap.tolist()] if detail_at_least(detail, DetailLevel.FULL) else None,
        summary={
            "rows": int(len(valid)),
            "price_source": str(params.price_source).lower(),
            "touch_band": band,
            "touch_mode": touch_mode,
            "cross_count": int(crosses.sum()),
            "band_touch_count": int(band_touches.sum()),
            "valid_vwap_rows": int(usable.sum()),
        },
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"volume_col": nf.used_fields.get("volume"), "touch_mode": touch_mode} if detail_at_least(detail, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="vwap.calculated", fields={"window": n, "last_value": last_value})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("vwap", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _price_series(df: pd.DataFrame, used: Dict[str, str], source: str) -> pd.Series:
    if source in ("typical", "hlc3"):
        return (df[used["high"]] + df[used["low"]] + df[used["close"]]) / 3.0
    if source == "ohlc4":
        return (df[used["open"]] + df[used["high"]] + df[used["low"]] + df[used["close"]]) / 4.0
    if source == "price":
        return df[used["price"]]
    return df[used["close"]]


def _crosses_zero(spread: pd.Series) -> pd.Series:
    prev = spread.shift(1)
    has_pair = spread.notna() & prev.notna()
    exact_touch = spread.eq(0)
    sign_change = ((spread > 0) & (prev < 0)) | ((spread < 0) & (prev > 0))
    return (exact_touch | (has_pair & sign_change)).fillna(False)


__all__ = ["VWAPParams", "VWAPRequest", "VWAPReport", "normalize_input", "run"]
