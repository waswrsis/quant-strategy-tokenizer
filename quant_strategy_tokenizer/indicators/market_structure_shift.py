"""
quant_strategy_tokenizer.indicators.market_structure_shift
===========================================================
Purpose: detect market structure shift from swing levels as an atomic token.
Core idea: Compare the latest close with the most recent swing high/low plus a breakout buffer. Assumes closes through prior structure can mark a structural shift.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, MarketStructureShiftParams, and ModuleRunContext.
Outputs: MarketStructureShiftReport with quality, last values, structure bias/state, nearest
support/resistance, levels, zones, signal, regime, optional series, input
profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
flat price when structure cannot be inferred, invalid profile bins, or invalid
zero-denominator calculations return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, order book, or live exchange
access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .structure_common import StructureParams, StructureReport, normalize_structure_input, run_structure_indicator


INDICATOR = 'market_structure_shift'
INPUT_KIND = 'ohlc'


@dataclass
class MarketStructureShiftParams(StructureParams):
    """Configuration for the market_structure_shift structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    breakout_buffer_pct: float = 0.002


@dataclass
class MarketStructureShiftRequest:
    data: Any
    params: MarketStructureShiftParams = field(default_factory=MarketStructureShiftParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MarketStructureShiftReport = StructureReport


def normalize_input(request: MarketStructureShiftRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: MarketStructureShiftRequest) -> ModuleResult[MarketStructureShiftReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MarketStructureShiftParams", "MarketStructureShiftRequest", "MarketStructureShiftReport", "normalize_input", "run"]
