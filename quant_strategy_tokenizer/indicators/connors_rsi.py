"""
quant_strategy_tokenizer.indicators.connors_rsi
===============================================
Purpose: Connors RSI composite momentum token.
Core idea: Average short RSI, streak RSI, and percent rank of short ROC. The implementation assumes combining level momentum, run-length pressure, and return rank gives a faster exhaustion signal.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ConnorsRSIParams, and ModuleRunContext.
Outputs: ConnorsRSIReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'connors_rsi'
INPUT_KIND = 'price'


@dataclass
class ConnorsRSIParams(MomentumParams):
    """Configuration for the connors_rsi momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    rsi_window: int = 3
    streak_rsi_window: int = 2
    rank_window: int = 100
    roc_window: int = 1
    overbought: float = 90.0
    oversold: float = 10.0


@dataclass
class ConnorsRSIRequest:
    data: Any
    params: ConnorsRSIParams = field(default_factory=ConnorsRSIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ConnorsRSIReport = MomentumReport


def normalize_input(request: ConnorsRSIRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ConnorsRSIRequest) -> ModuleResult[ConnorsRSIReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ConnorsRSIParams", "ConnorsRSIRequest", "ConnorsRSIReport", "normalize_input", "run"]
