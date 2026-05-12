"""
quant_strategy_tokenizer.indicators.linear_regression_r2
========================================================
Purpose: Rolling linear regression R-squared token.
Core idea: Fit a rolling least-squares line and return its R-squared. The implementation assumes higher linear fit quality means the trend is cleaner and less noisy.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, LinearRegressionR2Params, and ModuleRunContext.
Outputs: LinearRegressionR2Report with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'linear_regression_r2'
INPUT_KIND = 'price'


@dataclass
class LinearRegressionR2Params(TrendParams):
    """Configuration for the linear_regression_r2 trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class LinearRegressionR2Request:
    data: Any
    params: LinearRegressionR2Params = field(default_factory=LinearRegressionR2Params)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


LinearRegressionR2Report = TrendReport


def normalize_input(request: LinearRegressionR2Request):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: LinearRegressionR2Request) -> ModuleResult[LinearRegressionR2Report]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["LinearRegressionR2Params", "LinearRegressionR2Request", "LinearRegressionR2Report", "normalize_input", "run"]
