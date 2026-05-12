"""
quant_strategy_tokenizer.indicators.spike
=========================================
Purpose: detect abnormal range or return spikes in OHLC data.
Core idea: Compute recent true range or return magnitude and compare it with rolling baseline thresholds. Assumes unusually large recent movement can invalidate normal signal logic or require risk filtering.
Inputs: OHLC-like data, DataFrameSpec mapping, SpikeParams, optional ExtractorSpec, and ModuleRunContext.
Outputs: SpikeReport with spike flag, latest measures, threshold, optional series, warnings, and diagnostics.
Failure semantics: missing fields, invalid thresholds/windows, insufficient rows, or invalid numeric data return ModuleResult.fail.
Market generalization: spike detection uses generic price ranges and can apply to any bar-based market.
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
    indicator: str = "spike"
    last_value: Optional[float] = None
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    volatility_direction: str = "unknown"
    volatility_level: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
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
    normalized = None if max_ratio is None else min(100.0, 100.0 * max_ratio / float(p.multiplier))
    volatility_level = "extreme" if spike_count > 0 else "normal"
    report = SpikeReport(
        quality="ok",
        spike=bool(spike_count > 0),
        spike_count=spike_count,
        max_ratio=max_ratio,
        last_value=max_ratio,
        last_values={"value": max_ratio, "spike_count": float(spike_count)},
        volatility_direction="expanding" if spike_count > 0 else "stable",
        volatility_level=volatility_level,
        signal="spike" if spike_count > 0 else "normal",
        regime=volatility_level,
        normalized_value=normalized,
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
