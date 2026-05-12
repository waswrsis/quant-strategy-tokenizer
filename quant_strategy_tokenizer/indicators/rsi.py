"""
quant_strategy_tokenizer.indicators.rsi
=======================================
Purpose: Relative Strength Index momentum token.
Core idea: Compute Wilder-style average gains and losses, then map their ratio into a 0-100 oscillator. The implementation assumes persistent upside closes indicate bullish momentum and extreme readings can mark exhaustion.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, RSIParams, and ModuleRunContext.
Outputs: RSIReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'rsi'
INPUT_KIND = 'price'


@dataclass
class RSIParams(MomentumParams):
    """Configuration for the rsi momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = 70.0
    oversold: float = 30.0


@dataclass
class RSIRequest:
    data: Any
    params: RSIParams = field(default_factory=RSIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RSIReport = MomentumReport


def normalize_input(request: RSIRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: RSIRequest) -> ModuleResult[RSIReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RSIParams", "RSIRequest", "RSIReport", "normalize_input", "run"]
