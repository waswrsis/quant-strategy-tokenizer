"""
quant_strategy_tokenizer.indicators.narrow_range
=================================================
Purpose: detect narrow-range bars as an atomic structure token.
Core idea: Compare current high-low range with rolling average range. Assumes unusually small range signals compression.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, NarrowRangeParams, and ModuleRunContext.
Outputs: NarrowRangeReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'narrow_range'
INPUT_KIND = 'ohlc'


@dataclass
class NarrowRangeParams(StructureParams):
    """Configuration for the narrow_range structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20


@dataclass
class NarrowRangeRequest:
    data: Any
    params: NarrowRangeParams = field(default_factory=NarrowRangeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NarrowRangeReport = StructureReport


def normalize_input(request: NarrowRangeRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: NarrowRangeRequest) -> ModuleResult[NarrowRangeReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["NarrowRangeParams", "NarrowRangeRequest", "NarrowRangeReport", "normalize_input", "run"]
