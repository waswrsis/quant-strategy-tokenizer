"""
quant_strategy_tokenizer.indicators.false_breakout_detector
============================================================
Purpose: detect failed rolling-range breakouts as an atomic structure token.
Core idea: Search for recent breakouts that closed back inside the prior range. Assumes failed acceptance beyond a level can signal a sweep or trap.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, FalseBreakoutDetectorParams, and ModuleRunContext.
Outputs: FalseBreakoutDetectorReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'false_breakout_detector'
INPUT_KIND = 'ohlc'


@dataclass
class FalseBreakoutDetectorParams(StructureParams):
    """Configuration for the false_breakout_detector structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    retest_bars: int = 10


@dataclass
class FalseBreakoutDetectorRequest:
    data: Any
    params: FalseBreakoutDetectorParams = field(default_factory=FalseBreakoutDetectorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FalseBreakoutDetectorReport = StructureReport


def normalize_input(request: FalseBreakoutDetectorRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: FalseBreakoutDetectorRequest) -> ModuleResult[FalseBreakoutDetectorReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["FalseBreakoutDetectorParams", "FalseBreakoutDetectorRequest", "FalseBreakoutDetectorReport", "normalize_input", "run"]
