"""
quant_strategy_tokenizer.indicators.roc
=======================================
Purpose: Rate of Change momentum token.
Core idea: Calculate percentage change from the selected lookback ago. The implementation assumes percentage displacement is a scale-normalized momentum measure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ROCParams, and ModuleRunContext.
Outputs: ROCReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'roc'
INPUT_KIND = 'price'


@dataclass
class ROCParams(MomentumParams):
    """Configuration for the roc momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class ROCRequest:
    data: Any
    params: ROCParams = field(default_factory=ROCParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ROCReport = MomentumReport


def normalize_input(request: ROCRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ROCRequest) -> ModuleResult[ROCReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ROCParams", "ROCRequest", "ROCReport", "normalize_input", "run"]
