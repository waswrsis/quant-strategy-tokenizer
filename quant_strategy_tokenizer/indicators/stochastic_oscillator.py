"""
quant_strategy_tokenizer.indicators.stochastic_oscillator
=========================================================
Purpose: Slow stochastic oscillator momentum token.
Core idea: Compare close with the rolling high-low range, smooth %K, then smooth %D. The implementation assumes closes near the top of the recent range indicate bullish pressure and closes near the bottom indicate bearish pressure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, StochasticOscillatorParams, and ModuleRunContext.
Outputs: StochasticOscillatorReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'stochastic_oscillator'
INPUT_KIND = 'ohlc'


@dataclass
class StochasticOscillatorParams(MomentumParams):
    """Configuration for the stochastic_oscillator momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    stoch_window: int = 14
    smooth_k: int = 3
    smooth_d: int = 3
    overbought: float = 80.0
    oversold: float = 20.0


@dataclass
class StochasticOscillatorRequest:
    data: Any
    params: StochasticOscillatorParams = field(default_factory=StochasticOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StochasticOscillatorReport = MomentumReport


def normalize_input(request: StochasticOscillatorRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: StochasticOscillatorRequest) -> ModuleResult[StochasticOscillatorReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["StochasticOscillatorParams", "StochasticOscillatorRequest", "StochasticOscillatorReport", "normalize_input", "run"]
