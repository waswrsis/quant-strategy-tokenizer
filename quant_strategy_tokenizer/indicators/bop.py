"""
quant_strategy_tokenizer.indicators.bop
=======================================
Purpose: Balance of Power momentum token.
Core idea: Divide close-open by high-low to estimate whether buyers or sellers controlled the bar. The implementation assumes intrabar open-to-close progress relative to range captures pressure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, BOPParams, and ModuleRunContext.
Outputs: BOPReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'bop'
INPUT_KIND = 'ohlc_open'


@dataclass
class BOPParams(MomentumParams):
    """Configuration for the bop momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    overbought: float = 0.5
    oversold: float = -0.5


@dataclass
class BOPRequest:
    data: Any
    params: BOPParams = field(default_factory=BOPParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BOPReport = MomentumReport


def normalize_input(request: BOPRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: BOPRequest) -> ModuleResult[BOPReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["BOPParams", "BOPRequest", "BOPReport", "normalize_input", "run"]
