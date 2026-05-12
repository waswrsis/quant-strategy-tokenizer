"""
quant_strategy_tokenizer.indicators.time_series_forecast
========================================================
Purpose: Time Series Forecast trend token.
Core idea: Project the rolling regression line forward by a configurable number of periods. The implementation assumes the recent linear trend persists over the short forecast horizon.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TimeSeriesForecastParams, and ModuleRunContext.
Outputs: TimeSeriesForecastReport with quality, last values, trend direction, signal,
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


INDICATOR = 'time_series_forecast'
INPUT_KIND = 'price'


@dataclass
class TimeSeriesForecastParams(TrendParams):
    """Configuration for the time_series_forecast trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20
    forecast_periods: int = 1


@dataclass
class TimeSeriesForecastRequest:
    data: Any
    params: TimeSeriesForecastParams = field(default_factory=TimeSeriesForecastParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TimeSeriesForecastReport = TrendReport


def normalize_input(request: TimeSeriesForecastRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: TimeSeriesForecastRequest) -> ModuleResult[TimeSeriesForecastReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TimeSeriesForecastParams", "TimeSeriesForecastRequest", "TimeSeriesForecastReport", "normalize_input", "run"]
