"""
quant_strategy_tokenizer.indicators.spike
=================================
Module purpose: detect abnormal price ranges or returns relative to recent
volatility.
Core idea: normalize OHLC data, compute true range, compare recent bars against
a rolling ATR-like baseline, and report whether a spike is present.
Inputs: OHLC raw data, DataFrameSpec mapping, lookback, ATR window, multiplier,
and detail_level.
Outputs: SpikeReport with spike flag, count, max ratio, recent bars, and
diagnostics.
Failure semantics: missing OHLC or insufficient history returns explicit
failure, never a safe pass.
Market generalization: any OHLC market can use the detector; callers decide
what multiplier is appropriate for the asset and timeframe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class SpikeParams:
    """Spike detection options.

    Configuration:
    - `lookback_bars`: recent rows inspected for spike events.
    - `atr_window`: prior ATR window used to normalize true range.
    - `multiplier`: spike threshold; true range divided by prior ATR must reach
      this value.
    """

    lookback_bars: int = 10
    atr_window: int = 14
    multiplier: float = 3.0


@dataclass
class SpikeRequest:
    data: Any
    params: SpikeParams = field(default_factory=SpikeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="spike"))


@dataclass
class SpikeReport:
    quality: str
    spike: bool
    spike_count: int
    max_ratio: Optional[float]
    ratios: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: SpikeRequest):
    return normalize_frame(request.data, required_fields=["high", "low", "close"], spec=request.spec, extractor=request.extractor)


def run(request: SpikeRequest) -> ModuleResult[SpikeReport]:
    p = request.params
    lb = int(p.lookback_bars)
    n = int(p.atr_window)
    if lb <= 0 or n <= 0 or float(p.multiplier) <= 0:
        return ModuleResult.fail("invalid_parameter", "lookback, atr_window, and multiplier must be positive")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    h = nf.frame[nf.used_fields["high"]]
    l = nf.frame[nf.used_fields["low"]]
    c = nf.frame[nf.used_fields["close"]]
    if len(c.dropna()) < n + lb:
        return ModuleResult.fail("insufficient_data", f"need at least {n + lb} rows, got {len(c.dropna())}")
    prev = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    atr_ref = tr.rolling(n, min_periods=n).mean().shift(1)
    ratio = (tr / atr_ref.replace(0, pd.NA)).tail(lb)
    flags = ratio >= float(p.multiplier)
    spike_count = int(flags.fillna(False).sum())
    max_ratio = None if ratio.dropna().empty else float(ratio.max())
    report = SpikeReport(
        quality="ok",
        spike=bool(spike_count > 0),
        spike_count=spike_count,
        max_ratio=max_ratio,
        ratios=[None if pd.isna(x) else float(x) for x in ratio.tolist()] if detail_at_least(request.context.detail_level, DetailLevel.FULL) else None,
        summary={"lookback_bars": lb, "atr_window": n, "multiplier": float(p.multiplier)},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"method": "true_range_over_prior_rolling_mean"} if detail_at_least(request.context.detail_level, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="spike.evaluated", fields={"spike": bool(spike_count > 0), "count": spike_count})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("spike", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["SpikeParams", "SpikeRequest", "SpikeReport", "normalize_input", "run"]
