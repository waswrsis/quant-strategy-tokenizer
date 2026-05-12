"""
quant_strategy_tokenizer.indicators.break_of_structure
=======================================================
Purpose: detect break of structure from swing levels as an atomic token.
Core idea: Flag closes beyond the latest swing high or low. Assumes structure is broken only when close confirms beyond the level, not just wick movement.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, BreakOfStructureParams, and ModuleRunContext.
Outputs: BreakOfStructureReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'break_of_structure'
INPUT_KIND = 'ohlc'


@dataclass
class BreakOfStructureParams(StructureParams):
    """Configuration for the break_of_structure structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    breakout_buffer_pct: float = 0.002


@dataclass
class BreakOfStructureRequest:
    data: Any
    params: BreakOfStructureParams = field(default_factory=BreakOfStructureParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BreakOfStructureReport = StructureReport


def normalize_input(request: BreakOfStructureRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: BreakOfStructureRequest) -> ModuleResult[BreakOfStructureReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["BreakOfStructureParams", "BreakOfStructureRequest", "BreakOfStructureReport", "normalize_input", "run"]
