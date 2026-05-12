"""
quant_strategy_tokenizer.indicators.sma
=======================================
Purpose: Simple moving average trend token.
Core idea: Compute a rolling arithmetic mean of the selected price field. The implementation treats the moving average as a lagging fair-value line; price above it is bullish, price below it is bearish. It assumes bars are ordered, roughly comparable in spacing, and that a plain average is a useful baseline for trend direction.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, SMAParams, and ModuleRunContext.
Outputs: SMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'sma'
INPUT_KIND = 'price'


@dataclass
class SMAParams(TrendParams):
    """Configuration for the sma trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class SMARequest:
    data: Any
    params: SMAParams = field(default_factory=SMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SMAReport = TrendReport


def normalize_input(request: SMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: SMARequest) -> ModuleResult[SMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SMAParams", "SMARequest", "SMAReport", "normalize_input", "run"]
