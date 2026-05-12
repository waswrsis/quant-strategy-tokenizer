"""
quant_strategy_tokenizer.indicators.supertrend
==============================================
Module purpose: ATR-based Supertrend direction token.
Core idea: Build ATR bands around the median price and carry forward final bands to create a trailing trend line. The implementation assumes volatility-adjusted bands separate trend continuation from reversal noise.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, SupertrendParams, and ModuleRunContext.
Outputs: SupertrendReport with quality, last values, trend direction, signal,
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


INDICATOR = 'supertrend'
INPUT_KIND = 'ohlc'


@dataclass
class SupertrendParams(TrendParams):
    """Configuration for the supertrend trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    atr_window: int = 10
    multiplier: float = 3.0


@dataclass
class SupertrendRequest:
    data: Any
    params: SupertrendParams = field(default_factory=SupertrendParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SupertrendReport = TrendReport


def normalize_input(request: SupertrendRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: SupertrendRequest) -> ModuleResult[SupertrendReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SupertrendParams", "SupertrendRequest", "SupertrendReport", "normalize_input", "run"]
