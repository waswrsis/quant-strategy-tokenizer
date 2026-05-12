"""
quant_strategy_tokenizer.indicators.elder_ray
=============================================
Purpose: Elder Ray bull/bear power momentum token.
Core idea: Subtract an EMA baseline from high and low to estimate bull and bear power. The implementation assumes distance from a moving average reveals whether buyers or sellers can push beyond fair value.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ElderRayParams, and ModuleRunContext.
Outputs: ElderRayReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'elder_ray'
INPUT_KIND = 'ohlc'


@dataclass
class ElderRayParams(MomentumParams):
    """Configuration for the elder_ray momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 13
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class ElderRayRequest:
    data: Any
    params: ElderRayParams = field(default_factory=ElderRayParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ElderRayReport = MomentumReport


def normalize_input(request: ElderRayRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ElderRayRequest) -> ModuleResult[ElderRayReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ElderRayParams", "ElderRayRequest", "ElderRayReport", "normalize_input", "run"]
