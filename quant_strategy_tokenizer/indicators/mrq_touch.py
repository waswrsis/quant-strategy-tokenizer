"""
quant_strategy_tokenizer.indicators.mrq_touch
=====================================
Module purpose: evaluate mean-reversion quality by counting whether price
touches a reference band in recent history.
Core idea: normalize OHLC or close/reference data, build a reference band, and
report touch count, latest distance, and consecutive no-touch run.
Inputs: raw market data, DataFrameSpec mapping, lookback, band value, reference
mode, and detail_level.
Outputs: MRQTouchReport with pass/fail, touch count, no-touch run, distances,
and diagnostics.
Failure semantics: missing required fields or insufficient history returns
explicit failure. If no reference can be built, the module does not fail open.
Market generalization: works for any market with price observations; callers
choose the reference mode and band appropriate to the asset.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class MRQTouchParams:
    """Mean-reversion touch quality options.

    Configuration:
    - `lookback`: number of recent rows inspected for touches.
    - `min_touches`: minimum touches required to pass.
    - `band`: absolute distance around the reference counted as a touch.
    - `reference_field`: logical reference/fair-value field.
    - `price_field`: logical observed price field.
    """

    lookback: int = 120
    min_touches: int = 1
    band: float = 0.0
    reference_field: str = "close"
    price_field: str = "close"


@dataclass
class MRQTouchRequest:
    data: Any
    params: MRQTouchParams = field(default_factory=MRQTouchParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="mrq_touch"))


@dataclass
class MRQTouchReport:
    quality: str
    passed: bool
    touch_count: int
    no_touch_run: int
    last_distance: Optional[float]
    distances: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: MRQTouchRequest):
    fields = list({request.params.price_field, request.params.reference_field})
    return normalize_frame(request.data, required_fields=fields, spec=request.spec, extractor=request.extractor)


def run(request: MRQTouchRequest) -> ModuleResult[MRQTouchReport]:
    p = request.params
    lb = int(p.lookback)
    if lb <= 0:
        return ModuleResult.fail("invalid_parameter", "lookback must be positive", field="lookback")
    if int(p.min_touches) < 0:
        return ModuleResult.fail("invalid_parameter", "min_touches must be non-negative", field="min_touches")
    if int(p.min_touches) > lb:
        return ModuleResult.fail("invalid_parameter", "min_touches cannot exceed lookback", field="min_touches")
    if float(p.band) < 0:
        return ModuleResult.fail("invalid_parameter", "band must be non-negative", field="band")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    price = pd.to_numeric(nf.frame[nf.used_fields[p.price_field]], errors="coerce")
    ref = pd.to_numeric(nf.frame[nf.used_fields[p.reference_field]], errors="coerce")
    pair = pd.DataFrame({"price": price, "ref": ref}).dropna().tail(lb)
    if len(pair) < lb:
        return ModuleResult.fail("insufficient_data", f"need lookback rows after normalization: {lb}, got {len(pair)}")
    dist = (pair["price"] - pair["ref"]).abs()
    touches = dist <= float(p.band)
    no_touch_run = 0
    for flag in reversed(touches.tolist()):
        if flag:
            break
        no_touch_run += 1
    touch_count = int(touches.sum())
    passed = touch_count >= int(p.min_touches)
    report = MRQTouchReport(
        quality="ok",
        passed=bool(passed),
        touch_count=touch_count,
        no_touch_run=int(no_touch_run),
        last_distance=None if dist.empty or pd.isna(dist.iloc[-1]) else float(dist.iloc[-1]),
        distances=[None if pd.isna(x) else float(x) for x in dist.tolist()] if detail_at_least(request.context.detail_level, DetailLevel.FULL) else None,
        summary={"rows": int(len(pair)), "lookback": lb, "min_touches": int(p.min_touches), "band": float(p.band)},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"price_field": p.price_field, "reference_field": p.reference_field} if detail_at_least(request.context.detail_level, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="mrq_touch.evaluated", fields={"passed": passed, "touch_count": touch_count})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("mrq_touch", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["MRQTouchParams", "MRQTouchRequest", "MRQTouchReport", "normalize_input", "run"]
