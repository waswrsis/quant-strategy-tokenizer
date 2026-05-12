"""
quant_strategy_tokenizer.indicators.pivot_points
=================================================
Purpose: calculate classic pivot levels as an atomic structure token.
Core idea: Use prior high, low, and close to derive pivot, support, and resistance levels. Assumes the previous bar/session range can anchor current structure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PivotPointsParams, and ModuleRunContext.
Outputs: PivotPointsReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'pivot_points'
INPUT_KIND = 'ohlc'


@dataclass
class PivotPointsParams(StructureParams):
    """Configuration for the pivot_points structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20


@dataclass
class PivotPointsRequest:
    data: Any
    params: PivotPointsParams = field(default_factory=PivotPointsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PivotPointsReport = StructureReport


def normalize_input(request: PivotPointsRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: PivotPointsRequest) -> ModuleResult[PivotPointsReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PivotPointsParams", "PivotPointsRequest", "PivotPointsReport", "normalize_input", "run"]
