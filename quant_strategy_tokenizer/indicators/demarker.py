"""
quant_strategy_tokenizer.indicators.demarker
============================================
Purpose: DeMarker momentum exhaustion token.
Core idea: Compare recent high expansions with low contractions to form a bounded oscillator. The implementation assumes repeated higher highs or lower lows reveal directional exhaustion pressure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, DeMarkerParams, and ModuleRunContext.
Outputs: DeMarkerReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'demarker'
INPUT_KIND = 'ohlc'


@dataclass
class DeMarkerParams(MomentumParams):
    """Configuration for the demarker momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = 70.0
    oversold: float = 30.0


@dataclass
class DeMarkerRequest:
    data: Any
    params: DeMarkerParams = field(default_factory=DeMarkerParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DeMarkerReport = MomentumReport


def normalize_input(request: DeMarkerRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: DeMarkerRequest) -> ModuleResult[DeMarkerReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DeMarkerParams", "DeMarkerRequest", "DeMarkerReport", "normalize_input", "run"]
