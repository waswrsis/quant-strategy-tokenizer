"""
quant_strategy_tokenizer.indicators.cmo
=======================================
Purpose: Chande Momentum Oscillator token.
Core idea: Compare rolling sums of gains and losses as a signed oscillator. The implementation assumes net directional close-to-close pressure is more informative than absolute price level.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, CMOParams, and ModuleRunContext.
Outputs: CMOReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'cmo'
INPUT_KIND = 'price'


@dataclass
class CMOParams(MomentumParams):
    """Configuration for the cmo momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = 50.0
    oversold: float = -50.0


@dataclass
class CMORequest:
    data: Any
    params: CMOParams = field(default_factory=CMOParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


CMOReport = MomentumReport


def normalize_input(request: CMORequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: CMORequest) -> ModuleResult[CMOReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["CMOParams", "CMORequest", "CMOReport", "normalize_input", "run"]
