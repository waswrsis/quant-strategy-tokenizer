"""
quant_strategy_tokenizer.indicators.rolling_return
==================================================
Module purpose: calculate lagged or rolling returns from a caller-supplied value series.
Core idea: Normalize one value series and compare each row to a lagged value over a configured lookback. Assumes row order represents time order and percentage or absolute changes are sufficient for interval return features.
Inputs: value-series data, DataFrameSpec mapping, RollingReturnParams, optional ExtractorSpec, and ModuleRunContext.
Outputs: RollingReturnReport with latest return, optional series, summary, field mapping, and diagnostics.
Failure semantics: invalid lookback, missing value field, insufficient rows, zero denominator when needed, or invalid numeric data return ModuleResult.fail.
Market generalization: returns are computed from generic numeric values and are independent of instrument type.
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
class RollingReturnParams:
    """Rolling return calculation options.

    Configuration:
    - `lookback`: number of rows/bars between current and comparison value.
    - `mode`: `pct` for percentage return or `log` for log return.
    - `value_field`: logical price/value field resolved through `DataFrameSpec`.
    """

    lookback: int = 1
    mode: str = "pct"  # pct|log|diff
    value_field: str = "close"


@dataclass
class RollingReturnRequest:
    data: Any
    params: RollingReturnParams = field(default_factory=RollingReturnParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="rolling_return"))


@dataclass
class RollingReturnReport:
    quality: str
    lookback: int
    mode: str
    last_value: Optional[float]
    series: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def normalize_input(request: RollingReturnRequest):
    return normalize_frame(request.data, required_fields=[request.params.value_field], spec=request.spec, extractor=request.extractor)


def run(request: RollingReturnRequest) -> ModuleResult[RollingReturnReport]:
    p = request.params
    lb = int(p.lookback)
    if lb <= 0:
        return ModuleResult.fail("invalid_parameter", "lookback must be positive", field="lookback")
    norm = normalize_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    s = pd.to_numeric(nf.frame[nf.used_fields[p.value_field]], errors="coerce").dropna()
    if len(s) <= lb:
        return ModuleResult.fail("insufficient_data", f"need more than {lb} rows, got {len(s)}")
    mode = str(p.mode).lower()
    if mode == "log":
        if (s <= 0).any():
            return ModuleResult.fail("invalid_numeric", "log return requires positive values")
        ret = np.log(s / s.shift(lb))
    elif mode == "diff":
        ret = s - s.shift(lb)
    else:
        ret = s / s.shift(lb) - 1.0
    last = None if ret.empty or pd.isna(ret.iloc[-1]) else float(ret.iloc[-1])
    report = RollingReturnReport(
        quality="ok" if last is not None else "insufficient_data",
        lookback=lb,
        mode=mode,
        last_value=last,
        series=[None if pd.isna(x) else float(x) for x in ret.tolist()] if detail_at_least(request.context.detail_level, DetailLevel.FULL) else None,
        summary={"rows": int(len(s))},
        input_profile=nf.input_profile,
        used_fields=nf.used_fields,
        warnings=nf.warnings,
        diagnostics={"value_field": p.value_field} if detail_at_least(request.context.detail_level, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="rolling_return.calculated", fields={"lookback": lb, "last_value": last})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("rolling_return", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["RollingReturnParams", "RollingReturnRequest", "RollingReturnReport", "normalize_input", "run"]
