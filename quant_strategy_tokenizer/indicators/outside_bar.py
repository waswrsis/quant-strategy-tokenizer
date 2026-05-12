"""
quant_strategy_tokenizer.indicators.outside_bar
================================================
Purpose: detect outside bars as an atomic structure token.
Core idea: Check whether current high/low engulf the prior bar. Assumes outside bars represent short-term range expansion.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, OutsideBarParams, and ModuleRunContext.
Outputs: OutsideBarReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'outside_bar'
INPUT_KIND = 'ohlc'


@dataclass
class OutsideBarParams(StructureParams):
    """Configuration for the outside_bar structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20


@dataclass
class OutsideBarRequest:
    data: Any
    params: OutsideBarParams = field(default_factory=OutsideBarParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


OutsideBarReport = StructureReport


def normalize_input(request: OutsideBarRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: OutsideBarRequest) -> ModuleResult[OutsideBarReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["OutsideBarParams", "OutsideBarRequest", "OutsideBarReport", "normalize_input", "run"]
