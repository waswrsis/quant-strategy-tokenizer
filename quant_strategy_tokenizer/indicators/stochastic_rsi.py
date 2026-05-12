"""
quant_strategy_tokenizer.indicators.stochastic_rsi
==================================================
Purpose: Stochastic RSI momentum token.
Core idea: Compute RSI first, then normalize RSI within its own rolling min-max range. The implementation assumes momentum-of-momentum can reveal exhaustion earlier than price-based stochastic signals.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, StochasticRSIParams, and ModuleRunContext.
Outputs: StochasticRSIReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'stochastic_rsi'
INPUT_KIND = 'price'


@dataclass
class StochasticRSIParams(MomentumParams):
    """Configuration for the stochastic_rsi momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    rsi_window: int = 14
    stoch_window: int = 14
    smooth_k: int = 3
    smooth_d: int = 3
    overbought: float = 80.0
    oversold: float = 20.0


@dataclass
class StochasticRSIRequest:
    data: Any
    params: StochasticRSIParams = field(default_factory=StochasticRSIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StochasticRSIReport = MomentumReport


def normalize_input(request: StochasticRSIRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: StochasticRSIRequest) -> ModuleResult[StochasticRSIReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["StochasticRSIParams", "StochasticRSIRequest", "StochasticRSIReport", "normalize_input", "run"]
