"""
quant_strategy_tokenizer.indicators.linear_regression_slope
===========================================================
Purpose: Rolling linear regression slope token.
Core idea: Fit a rolling least-squares line and return its slope. The implementation assumes slope is the direct directional speed of the local trend.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, LinearRegressionSlopeParams, and ModuleRunContext.
Outputs: LinearRegressionSlopeReport with quality, last values, trend direction, signal,
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


INDICATOR = 'linear_regression_slope'
INPUT_KIND = 'price'


@dataclass
class LinearRegressionSlopeParams(TrendParams):
    """Configuration for the linear_regression_slope trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class LinearRegressionSlopeRequest:
    data: Any
    params: LinearRegressionSlopeParams = field(default_factory=LinearRegressionSlopeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


LinearRegressionSlopeReport = TrendReport


def normalize_input(request: LinearRegressionSlopeRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: LinearRegressionSlopeRequest) -> ModuleResult[LinearRegressionSlopeReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["LinearRegressionSlopeParams", "LinearRegressionSlopeRequest", "LinearRegressionSlopeReport", "normalize_input", "run"]
