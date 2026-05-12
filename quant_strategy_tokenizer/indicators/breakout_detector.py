"""
quant_strategy_tokenizer.indicators.breakout_detector
======================================================
Purpose: detect rolling-range breakout or breakdown as an atomic structure token.
Core idea: Compare close with prior rolling high/low plus a buffer. Assumes close confirmation reduces false wick-only breakouts.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, BreakoutDetectorParams, and ModuleRunContext.
Outputs: BreakoutDetectorReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'breakout_detector'
INPUT_KIND = 'ohlc'


@dataclass
class BreakoutDetectorParams(StructureParams):
    """Configuration for the breakout_detector structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    breakout_buffer_pct: float = 0.002


@dataclass
class BreakoutDetectorRequest:
    data: Any
    params: BreakoutDetectorParams = field(default_factory=BreakoutDetectorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BreakoutDetectorReport = StructureReport


def normalize_input(request: BreakoutDetectorRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: BreakoutDetectorRequest) -> ModuleResult[BreakoutDetectorReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["BreakoutDetectorParams", "BreakoutDetectorRequest", "BreakoutDetectorReport", "normalize_input", "run"]
