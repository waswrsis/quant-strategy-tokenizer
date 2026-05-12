"""
quant_strategy_tokenizer.indicators.support_resistance_zones
=============================================================
Purpose: build support and resistance zones from clustered levels as an atomic token.
Core idea: Expand clustered levels by zone_width_pct into zones. Assumes actionable structure is often an area rather than a single exact price.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, SupportResistanceZonesParams, and ModuleRunContext.
Outputs: SupportResistanceZonesReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'support_resistance_zones'
INPUT_KIND = 'ohlc'


@dataclass
class SupportResistanceZonesParams(StructureParams):
    """Configuration for the support_resistance_zones structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    zone_width_pct: float = 0.005


@dataclass
class SupportResistanceZonesRequest:
    data: Any
    params: SupportResistanceZonesParams = field(default_factory=SupportResistanceZonesParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SupportResistanceZonesReport = StructureReport


def normalize_input(request: SupportResistanceZonesRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: SupportResistanceZonesRequest) -> ModuleResult[SupportResistanceZonesReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SupportResistanceZonesParams", "SupportResistanceZonesRequest", "SupportResistanceZonesReport", "normalize_input", "run"]
