"""
quant_strategy_tokenizer.indicators.chop
================================
Module purpose: calculate the Choppiness Index from OHLC data.
Core idea: compare rolling summed true range with rolling high-low range to
estimate whether movement is directional or choppy.
Inputs: OHLC raw data, DataFrameSpec mapping, window, detail_level.
Outputs: CHOPReport with last CHOP, optional series, input mapping, and
diagnostics.
Failure semantics: missing OHLC, non-positive rolling range, or insufficient
rows returns explicit failure.
Market generalization: works for any OHLC market; no exchange or asset-class
assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class CHOPParams:
    """Choppiness index calculation options.

    Configuration:
    - `window`: lookback in rows/bars used for true-range sum and high-low
      range. Larger values smooth the regime score.
    """

    window: int = 14


@dataclass
class CHOPRequest:
    data: Any
    params: CHOPParams = field(default_factory=CHOPParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="chop"))


@dataclass
class CHOPReport:
    quality: str
    window: int
    last_value: Optional[float]
    series: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: CHOPRequest):
    return normalize_frame(request.data, required_fields=["high", "low", "close"], spec=request.spec, extractor=request.extractor)


def run(request: CHOPRequest) -> ModuleResult[CHOPReport]:
    n = int(request.params.window)
    if n <= 1:
        return ModuleResult.fail("invalid_parameter", "CHOP window must be greater than 1", field="window")
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
        return ModuleResult.fail("insufficient_data", f"need at least {n + 1} rows, got {len(c.dropna())}")
    prev = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    tr_sum = tr.rolling(n, min_periods=n).sum()
    rng = h.rolling(n, min_periods=n).max() - l.rolling(n, min_periods=n).min()
    chop = 100.0 * np.log10((tr_sum / rng.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)) / np.log10(n)
    last = None if chop.empty or pd.isna(chop.iloc[-1]) else float(chop.iloc[-1])
    detail = request.context.detail_level
    report = CHOPReport(
        quality="ok" if last is not None else "insufficient_data",
        window=n,
        last_value=last,
        series=[None if pd.isna(x) else float(x) for x in chop.tolist()] if detail_at_least(detail, DetailLevel.FULL) else None,
        summary={"rows": int(len(c))},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"formula": "100*log10(sum(TR)/range)/log10(window)"} if detail_at_least(detail, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="chop.calculated", fields={"window": n, "last_value": last})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("chop", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["CHOPParams", "CHOPRequest", "CHOPReport", "normalize_input", "run"]
