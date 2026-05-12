"""
quant_strategy_tokenizer.indicators.zigzag_structure
=====================================================
Purpose: extract percent-threshold zigzag structure as an atomic token.
Core idea: Mark directional pivots after price reverses by swing_threshold_pct. Assumes small swings should be ignored until price moves enough to define structure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ZigzagStructureParams, and ModuleRunContext.
Outputs: ZigzagStructureReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'zigzag_structure'
INPUT_KIND = 'ohlc'


@dataclass
class ZigzagStructureParams(StructureParams):
    """Configuration for the zigzag_structure structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    swing_threshold_pct: float = 0.02


@dataclass
class ZigzagStructureRequest:
    data: Any
    params: ZigzagStructureParams = field(default_factory=ZigzagStructureParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ZigzagStructureReport = StructureReport


def normalize_input(request: ZigzagStructureRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: ZigzagStructureRequest) -> ModuleResult[ZigzagStructureReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ZigzagStructureParams", "ZigzagStructureRequest", "ZigzagStructureReport", "normalize_input", "run"]
