"""
quant_strategy_tokenizer.indicators.rocr
========================================
Purpose: Rate of Change Ratio momentum token.
Core idea: Calculate current price divided by the price from the selected lookback ago. The implementation assumes a neutral value of 1.0, above which momentum is positive and below which it is negative.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ROCRParams, and ModuleRunContext.
Outputs: ROCRReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'rocr'
INPUT_KIND = 'price'


@dataclass
class ROCRParams(MomentumParams):
    """Configuration for the rocr momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 1.0
    oversold: float = 1.0


@dataclass
class ROCRRequest:
    data: Any
    params: ROCRParams = field(default_factory=ROCRParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ROCRReport = MomentumReport


def normalize_input(request: ROCRRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ROCRRequest) -> ModuleResult[ROCRReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ROCRParams", "ROCRRequest", "ROCRReport", "normalize_input", "run"]
