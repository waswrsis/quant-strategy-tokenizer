"""
quant_strategy_tokenizer.indicators.stochastic_fast
===================================================
Purpose: Fast stochastic oscillator momentum token.
Core idea: Compute unsmoothed stochastic %K and a short %D signal line. The implementation assumes raw range position is useful when the caller wants faster but noisier momentum turns.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, StochasticFastParams, and ModuleRunContext.
Outputs: StochasticFastReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'stochastic_fast'
INPUT_KIND = 'ohlc'


@dataclass
class StochasticFastParams(MomentumParams):
    """Configuration for the stochastic_fast momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    stoch_window: int = 14
    smooth_d: int = 3
    overbought: float = 80.0
    oversold: float = 20.0


@dataclass
class StochasticFastRequest:
    data: Any
    params: StochasticFastParams = field(default_factory=StochasticFastParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StochasticFastReport = MomentumReport


def normalize_input(request: StochasticFastRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: StochasticFastRequest) -> ModuleResult[StochasticFastReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["StochasticFastParams", "StochasticFastRequest", "StochasticFastReport", "normalize_input", "run"]
