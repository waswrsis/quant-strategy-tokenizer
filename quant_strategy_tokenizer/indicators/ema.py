"""
quant_strategy_tokenizer.indicators.ema
===============================
Module purpose: calculate an exponential moving average from raw or normalized
price data.
Core idea: normalize user input into a single value series, then apply pandas
ewm with configurable span.
Inputs: DataFrame/Series/list/dict/custom object, DataFrameSpec value/close
mapping, window, min_periods, detail_level, and optional output_dir.
Outputs: EMAReport with last value, full/partial series by detail level,
input mapping, quality, and diagnostics.
Failure semantics: missing value field, invalid numeric data, or insufficient
rows returns ModuleResult.fail; no implicit column guessing unless aliases are
enabled in DataFrameSpec.
Market generalization: any market with a numeric price or value series can use
this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..normalization import normalize_frame
from ..reporting import write_module_report


@dataclass
class EMAParams:
    """EMA calculation options.

    Configuration:
    - `window`: exponential moving average span in rows/bars.
    - `min_periods`: minimum numeric rows before output is valid; `None` uses
      `window`.
    - `adjust`: passed to pandas `ewm`; False gives recursive trading-style EMA.
    - `value_field`: logical field to average, resolved through `DataFrameSpec`.
    """

    window: int = 20
    min_periods: Optional[int] = None
    adjust: bool = False
    value_field: str = "close"


@dataclass
class EMARequest:
    data: Any
    params: EMAParams = field(default_factory=EMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="ema"))


@dataclass
class EMAReport:
    quality: str
    window: int
    last_value: Optional[float]
    series: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: EMARequest):
    return normalize_frame(request.data, required_fields=[request.params.value_field], spec=request.spec, extractor=request.extractor)


def run(request: EMARequest) -> ModuleResult[EMAReport]:
    params = request.params
    if int(params.window) <= 0:
        return ModuleResult.fail("invalid_parameter", "EMA window must be positive", field="window")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    value_col = nf.used_fields[params.value_field]
    values = pd.to_numeric(nf.frame[value_col], errors="coerce").dropna()
    min_periods = int(params.min_periods if params.min_periods is not None else params.window)
    if len(values) < min_periods:
        return ModuleResult.fail("insufficient_data", f"need at least {min_periods} numeric rows, got {len(values)}")
    ema_series = values.ewm(span=int(params.window), adjust=bool(params.adjust), min_periods=min_periods).mean()
    last = None if ema_series.empty or pd.isna(ema_series.iloc[-1]) else float(ema_series.iloc[-1])
    detail = request.context.detail_level
    series_out = None
    if detail_at_least(detail, DetailLevel.FULL):
        series_out = [None if pd.isna(x) else float(x) for x in ema_series.tolist()]
    report = EMAReport(
        quality="ok" if last is not None else "insufficient_data",
        window=int(params.window),
        last_value=last,
        series=series_out,
        summary={"rows": int(len(values)), "min_periods": min_periods},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        missing_fields=nf.missing_fields,
        warnings=nf.warnings,
        diagnostics={"value_col": value_col, "adjust": bool(params.adjust)} if detail_at_least(detail, DetailLevel.STANDARD) else {},
    )
    events = [ModuleEvent(event="ema.calculated", fields={"window": int(params.window), "last_value": last})]
    result = ModuleResult.success(report, events=events, warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("ema", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["EMAParams", "EMARequest", "EMAReport", "normalize_input", "run"]
