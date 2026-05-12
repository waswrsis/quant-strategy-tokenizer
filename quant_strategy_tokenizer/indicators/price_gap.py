"""
quant_strategy_tokenizer.indicators.price_gap
==============================================
Purpose: detect opening price gaps as an atomic structure token.
Core idea: Compare open with prior close as a percentage gap. Assumes discontinuous jumps deserve separate structural treatment from intrabar range.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PriceGapParams, and ModuleRunContext.
Outputs: PriceGapReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'price_gap'
INPUT_KIND = 'ohlc_open'


@dataclass
class PriceGapParams(StructureParams):
    """Configuration for the price_gap structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    min_gap_pct: float = 0.001


@dataclass
class PriceGapRequest:
    data: Any
    params: PriceGapParams = field(default_factory=PriceGapParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PriceGapReport = StructureReport


def normalize_input(request: PriceGapRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: PriceGapRequest) -> ModuleResult[PriceGapReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PriceGapParams", "PriceGapRequest", "PriceGapReport", "normalize_input", "run"]
