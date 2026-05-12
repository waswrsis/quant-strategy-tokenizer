"""
quant_strategy_tokenizer.indicators.kdj
=======================================
Purpose: KDJ stochastic momentum token.
Core idea: Recursively smooth stochastic RSV into K and D, then derive J as an amplified spread. The implementation assumes J highlights momentum extremes beyond the slower K/D state.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, KDJParams, and ModuleRunContext.
Outputs: KDJReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'kdj'
INPUT_KIND = 'ohlc'


@dataclass
class KDJParams(MomentumParams):
    """Configuration for the kdj momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    stoch_window: int = 9
    smooth_k: int = 3
    smooth_d: int = 3
    overbought: float = 80.0
    oversold: float = 20.0


@dataclass
class KDJRequest:
    data: Any
    params: KDJParams = field(default_factory=KDJParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


KDJReport = MomentumReport


def normalize_input(request: KDJRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: KDJRequest) -> ModuleResult[KDJReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["KDJParams", "KDJRequest", "KDJReport", "normalize_input", "run"]
