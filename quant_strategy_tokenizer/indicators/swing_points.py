"""
quant_strategy_tokenizer.indicators.swing_points
=================================================
Purpose: detect local swing highs and lows as an atomic structure token.
Core idea: Compare each high/low with configurable left and right neighbors. Assumes local extrema are useful primitive structure points but not trade signals by themselves.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, SwingPointsParams, and ModuleRunContext.
Outputs: SwingPointsReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'swing_points'
INPUT_KIND = 'ohlc'


@dataclass
class SwingPointsParams(StructureParams):
    """Configuration for the swing_points structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    left_bars: int = 3
    right_bars: int = 3


@dataclass
class SwingPointsRequest:
    data: Any
    params: SwingPointsParams = field(default_factory=SwingPointsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SwingPointsReport = StructureReport


def normalize_input(request: SwingPointsRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: SwingPointsRequest) -> ModuleResult[SwingPointsReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SwingPointsParams", "SwingPointsRequest", "SwingPointsReport", "normalize_input", "run"]
