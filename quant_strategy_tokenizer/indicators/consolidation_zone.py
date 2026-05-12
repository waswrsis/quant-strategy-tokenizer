"""
quant_strategy_tokenizer.indicators.consolidation_zone
=======================================================
Purpose: detect rolling consolidation zones as an atomic structure token.
Core idea: Compare range width with its own historical compression. Assumes unusually narrow boxes indicate consolidation.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ConsolidationZoneParams, and ModuleRunContext.
Outputs: ConsolidationZoneReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'consolidation_zone'
INPUT_KIND = 'ohlc'


@dataclass
class ConsolidationZoneParams(StructureParams):
    """Configuration for the consolidation_zone structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    lookback: int = 120


@dataclass
class ConsolidationZoneRequest:
    data: Any
    params: ConsolidationZoneParams = field(default_factory=ConsolidationZoneParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ConsolidationZoneReport = StructureReport


def normalize_input(request: ConsolidationZoneRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: ConsolidationZoneRequest) -> ModuleResult[ConsolidationZoneReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ConsolidationZoneParams", "ConsolidationZoneRequest", "ConsolidationZoneReport", "normalize_input", "run"]
