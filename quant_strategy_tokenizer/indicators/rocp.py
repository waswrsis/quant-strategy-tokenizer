"""
quant_strategy_tokenizer.indicators.rocp
========================================
Purpose: Fractional Rate of Change momentum token.
Core idea: Calculate fractional change from the selected lookback ago. The implementation assumes raw decimal returns are easier for downstream models than percent-form ROC.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ROCPParams, and ModuleRunContext.
Outputs: ROCPReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'rocp'
INPUT_KIND = 'price'


@dataclass
class ROCPParams(MomentumParams):
    """Configuration for the rocp momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class ROCPRequest:
    data: Any
    params: ROCPParams = field(default_factory=ROCPParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ROCPReport = MomentumReport


def normalize_input(request: ROCPRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ROCPRequest) -> ModuleResult[ROCPReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ROCPParams", "ROCPRequest", "ROCPReport", "normalize_input", "run"]
