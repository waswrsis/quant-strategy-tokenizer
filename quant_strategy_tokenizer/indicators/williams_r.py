"""
quant_strategy_tokenizer.indicators.williams_r
==============================================
Purpose: Williams percent-R momentum token.
Core idea: Measure close location relative to the rolling high-low range on a -100 to 0 scale. The implementation assumes closes near recent highs show bullish pressure and closes near recent lows show bearish exhaustion.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, WilliamsRParams, and ModuleRunContext.
Outputs: WilliamsRReport with quality, last values, momentum direction, signal,
zone, optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .momentum_common import MomentumParams, MomentumReport, normalize_momentum_input, run_momentum_indicator


INDICATOR = 'williams_r'
INPUT_KIND = 'ohlc'


@dataclass
class WilliamsRParams(MomentumParams):
    """Configuration for the williams_r momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = -20.0
    oversold: float = -80.0


@dataclass
class WilliamsRRequest:
    data: Any
    params: WilliamsRParams = field(default_factory=WilliamsRParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


WilliamsRReport = MomentumReport


def normalize_input(request: WilliamsRRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: WilliamsRRequest) -> ModuleResult[WilliamsRReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["WilliamsRParams", "WilliamsRRequest", "WilliamsRReport", "normalize_input", "run"]
