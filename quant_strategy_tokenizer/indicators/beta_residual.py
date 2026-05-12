"""
quant_strategy_tokenizer.indicators.beta_residual
=================================================
Module purpose: estimate beta-adjusted residual movement against a benchmark series.
Core idea: Align asset and benchmark series by row order, run rolling or windowed linear regression, and report residuals from the fitted relationship. Assumes the benchmark explains a linear component of the asset move and the leftover residual is useful as relative strength/dispersion.
Inputs: asset series, benchmark series, field mapping params, BetaResidualParams, and ModuleRunContext.
Outputs: BetaResidualReport with beta, alpha, residual, optional series, summary, warnings, and diagnostics.
Failure semantics: missing fields, insufficient aligned rows, zero-variance benchmark, or invalid numeric data return ModuleResult.fail.
Market generalization: works for any two comparable numeric series supplied by the caller.
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
class BetaResidualParams:
    """Pair regression and residual options.

    Configuration:
    - `window`: number of aligned rows used for regression.
    - `y_field`: dependent series logical field in `y_data`.
    - `x_field`: independent/benchmark series logical field in `x_data`.
    """

    window: int = 60
    y_field: str = "close"
    x_field: str = "close"


@dataclass
class BetaResidualRequest:
    y_data: Any
    x_data: Any
    params: BetaResidualParams = field(default_factory=BetaResidualParams)
    y_spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    x_spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    y_extractor: Optional[ExtractorSpec] = None
    x_extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="beta_residual"))


@dataclass
class BetaResidualReport:
    quality: str
    beta: Optional[float]
    alpha: Optional[float]
    corr: Optional[float]
    r2: Optional[float]
    residual_last: Optional[float]
    residual_z: Optional[float]
    residual_slope: Optional[float]
    residual_series: Optional[List[Optional[float]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, Dict[str, str]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def run(request: BetaResidualRequest) -> ModuleResult[BetaResidualReport]:
    p = request.params
    n = int(p.window)
    if n <= 2:
        return ModuleResult.fail("invalid_parameter", "window must be greater than 2", field="window")
    yn = normalize_frame(request.y_data, required_fields=[p.y_field], spec=request.y_spec, extractor=request.y_extractor)
    xn = normalize_frame(request.x_data, required_fields=[p.x_field], spec=request.x_spec, extractor=request.x_extractor)
    if not yn.ok:
        return ModuleResult.fail(yn.failure.kind, yn.failure.message, field=f"y.{yn.failure.field}", details=yn.failure.details)
    if not xn.ok:
        return ModuleResult.fail(xn.failure.kind, xn.failure.message, field=f"x.{xn.failure.field}", details=xn.failure.details)
    yf = yn.value
    xf = xn.value
    if yf is None or xf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    y = pd.to_numeric(yf.frame[yf.used_fields[p.y_field]], errors="coerce").reset_index(drop=True)
    x = pd.to_numeric(xf.frame[xf.used_fields[p.x_field]], errors="coerce").reset_index(drop=True)
    m = min(len(y), len(x))
    pair = pd.DataFrame({"y": y.iloc[-m:], "x": x.iloc[-m:]}).dropna().tail(n)
    if len(pair) < n:
        return ModuleResult.fail("insufficient_data", f"need {n} overlapping rows, got {len(pair)}")
    xv = pair["x"].to_numpy(dtype=float)
    yv = pair["y"].to_numpy(dtype=float)
    if float(np.var(xv)) <= 0:
        return ModuleResult.fail("invalid_numeric", "x variance is zero")
    beta, alpha = np.polyfit(xv, yv, 1)
    fitted = alpha + beta * xv
    resid = yv - fitted
    corr = float(np.corrcoef(xv, yv)[0, 1]) if len(pair) > 1 else None
    r2 = None if corr is None or not np.isfinite(corr) else float(corr * corr)
    resid_std = float(np.std(resid, ddof=1)) if len(resid) > 1 else 0.0
    resid_z = None if resid_std <= 0 else float((resid[-1] - float(np.mean(resid))) / resid_std)
    slope = float(np.polyfit(np.arange(len(resid)), resid, 1)[0]) if len(resid) > 1 else 0.0
    report = BetaResidualReport(
        quality="ok",
        beta=float(beta),
        alpha=float(alpha),
        corr=corr,
        r2=r2,
        residual_last=float(resid[-1]),
        residual_z=resid_z,
        residual_slope=slope,
        residual_series=[float(v) for v in resid.tolist()] if detail_at_least(request.context.detail_level, DetailLevel.FULL) else None,
        summary={"rows": int(len(pair)), "window": n},
        input_profile={"y": yf.input_profile, "x": xf.input_profile},
        used_fields={"y": yf.used_fields, "x": xf.used_fields},
        warnings=list(yn.warnings or []) + list(xn.warnings or []),
        diagnostics={"method": "least_squares"} if detail_at_least(request.context.detail_level, DetailLevel.STANDARD) else {},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="beta_residual.calculated", fields={"beta": float(beta), "corr": corr})], warnings=report.warnings)
    if request.context.output_dir:
        result.files = write_module_report("beta_residual", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["BetaResidualParams", "BetaResidualRequest", "BetaResidualReport", "run"]
