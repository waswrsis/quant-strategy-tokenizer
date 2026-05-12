"""
quant_strategy_tokenizer.indicators.range_position
===================================================
Purpose: locate close inside the rolling range box as an atomic structure token.
Core idea: Normalize close between rolling support and resistance. Assumes relative box location is more reusable than raw price.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RangePositionParams, and ModuleRunContext.
Outputs: RangePositionReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'range_position'
INPUT_KIND = 'ohlc'


@dataclass
class RangePositionParams(StructureParams):
    """Configuration for the range_position structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20


@dataclass
class RangePositionRequest:
    data: Any
    params: RangePositionParams = field(default_factory=RangePositionParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RangePositionReport = StructureReport


def normalize_input(request: RangePositionRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: RangePositionRequest) -> ModuleResult[RangePositionReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RangePositionParams", "RangePositionRequest", "RangePositionReport", "normalize_input", "run"]
