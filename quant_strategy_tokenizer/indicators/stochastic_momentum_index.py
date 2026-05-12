"""
quant_strategy_tokenizer.indicators.stochastic_momentum_index
=============================================================
Purpose: Stochastic Momentum Index token.
Core idea: Compare close with the midpoint of the rolling high-low range and double-smooth both distance and range. The implementation assumes midpoint distance is a less jumpy stochastic momentum measure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, StochasticMomentumIndexParams, and ModuleRunContext.
Outputs: StochasticMomentumIndexReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'stochastic_momentum_index'
INPUT_KIND = 'ohlc'


@dataclass
class StochasticMomentumIndexParams(MomentumParams):
    """Configuration for the stochastic_momentum_index momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    stoch_window: int = 14
    smooth_k: int = 3
    smooth_d: int = 3
    signal_window: int = 3
    overbought: float = 40.0
    oversold: float = -40.0


@dataclass
class StochasticMomentumIndexRequest:
    data: Any
    params: StochasticMomentumIndexParams = field(default_factory=StochasticMomentumIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StochasticMomentumIndexReport = MomentumReport


def normalize_input(request: StochasticMomentumIndexRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: StochasticMomentumIndexRequest) -> ModuleResult[StochasticMomentumIndexReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["StochasticMomentumIndexParams", "StochasticMomentumIndexRequest", "StochasticMomentumIndexReport", "normalize_input", "run"]
