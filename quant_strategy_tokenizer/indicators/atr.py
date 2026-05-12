"""
quant_strategy_tokenizer.indicators.atr
=======================================
Module purpose: calculate Average True Range from caller-supplied OHLC data.
Core idea: Compute true range from high-low and prior-close gaps, then smooth it with Wilder RMA or a configured moving average. Assumes gaps and intrabar range jointly describe volatility risk.
Inputs: OHLC-like data, DataFrameSpec mapping, ATRParams, optional ExtractorSpec, and ModuleRunContext.
Outputs: ATRReport with latest ATR, optional series, summary, used fields, warnings, and diagnostics.
Failure semantics: missing OHLC fields, invalid window, insufficient rows, or invalid numeric data return ModuleResult.fail.
Market generalization: ATR uses generic OHLC fields and does not assume exchange sessions or asset class.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class ATRParams:
    """Average true range calculation options.

    Configuration:
    - `window`: ATR lookback in rows/bars.
    - `smoothing`: `rma` for Wilder-style smoothing or `sma` for simple
      rolling mean.
    """

    window: int = 14
    smoothing: str = "rma"


@dataclass
class ATRRequest:
    data: Any
    params: ATRParams = field(default_factory=ATRParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="atr"))


@dataclass
class ATRReport:
    quality: str
    window: int
    last_value: Optional[float]
    series: Optional[List[Optional[float]]] = None
    true_range_last: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: ATRRequest):
    return normalize_frame(request.data, required_fields=["high", "low", "close"], spec=request.spec, extractor=request.extractor)


def run(request: ATRRequest) -> ModuleResult[ATRReport]:
    params = request.params
    n = int(params.window)
    if n <= 0:
        return ModuleResult.fail("invalid_parameter", "ATR window must be positive", field="window")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    h = nf.frame[nf.used_fields["high"]]
    l = nf.frame[nf.used_fields["low"]]
    c = nf.frame[nf.used_fields["close"]]
    if len(c.dropna()) < n + 1:
        return ModuleResult.fail("insufficient_data", f"need at least {n + 1} close rows, got {len(c.dropna())}")
    prev_close = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev_close).abs(), (l - prev_close).abs()], axis=1).max(axis=1)
    if str(params.smoothing).lower() == "sma":
        atr = tr.rolling(n, min_periods=n).mean()
    else:
        atr = tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    last = None if atr.empty or pd.isna(atr.iloc[-1]) else float(atr.iloc[-1])
    detail = request.context.detail_level
    report = ATRReport(
        quality="ok" if last is not None else "insufficient_data",
        window=n,
        last_value=last,
        series=[None if pd.isna(x) else float(x) for x in atr.tolist()] if detail_at_least(detail, DetailLevel.FULL) else None,
        true_range_last=None if tr.empty or pd.isna(tr.iloc[-1]) else float(tr.iloc[-1]),
        summary={"rows": int(len(c)), "smoothing": str(params.smoothing).lower()},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"required_fields": ["high", "low", "close"]} if detail_at_least(detail, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="atr.calculated", fields={"window": n, "last_value": last})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("atr", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["ATRParams", "ATRRequest", "ATRReport", "normalize_input", "run"]
