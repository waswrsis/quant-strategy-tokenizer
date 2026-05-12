"""
quant_strategy_tokenizer.indicators.fair_value_gap
===================================================
Purpose: detect three-bar fair-value-gap style gaps as an atomic structure token.
Core idea: Compare current low/high with the bar two periods back. Assumes untraded-looking gaps in OHLC bars are only an approximation, not footprint data.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, FairValueGapParams, and ModuleRunContext.
Outputs: FairValueGapReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'fair_value_gap'
INPUT_KIND = 'ohlc'


@dataclass
class FairValueGapParams(StructureParams):
    """Configuration for the fair_value_gap structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    min_gap_pct: float = 0.001


@dataclass
class FairValueGapRequest:
    data: Any
    params: FairValueGapParams = field(default_factory=FairValueGapParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FairValueGapReport = StructureReport


def normalize_input(request: FairValueGapRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: FairValueGapRequest) -> ModuleResult[FairValueGapReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["FairValueGapParams", "FairValueGapRequest", "FairValueGapReport", "normalize_input", "run"]
