"""
quant_strategy_tokenizer.indicators.momentum
============================================
Purpose: Raw price momentum token.
Core idea: Subtract the price from a fixed lookback ago from the current price. The implementation assumes signed price displacement over the lookback is the simplest direct momentum measure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MomentumParams, and ModuleRunContext.
Outputs: MomentumReport with quality, last values, momentum direction, signal,
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
from .momentum_common import MomentumParams as BaseMomentumParams
from .momentum_common import MomentumReport as BaseMomentumReport
from .momentum_common import normalize_momentum_input, run_momentum_indicator


INDICATOR = 'momentum'
INPUT_KIND = 'price'


@dataclass
class MomentumParams(BaseMomentumParams):
    """Configuration for the momentum momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class MomentumRequest:
    data: Any
    params: MomentumParams = field(default_factory=MomentumParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MomentumReport = BaseMomentumReport


def normalize_input(request: MomentumRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: MomentumRequest) -> ModuleResult[MomentumReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MomentumParams", "MomentumRequest", "MomentumReport", "normalize_input", "run"]
