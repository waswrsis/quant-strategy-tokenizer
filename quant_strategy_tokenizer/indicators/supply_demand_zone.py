"""
quant_strategy_tokenizer.indicators.supply_demand_zone
=======================================================
Purpose: estimate supply and demand zones from OHLCV as an atomic structure token.
Core idea: Use large range impulses to label nearby prior bars as supply or demand zones. Assumes this is a reusable OHLCV zone approximation.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, SupplyDemandZoneParams, and ModuleRunContext.
Outputs: SupplyDemandZoneReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'supply_demand_zone'
INPUT_KIND = 'ohlcv'


@dataclass
class SupplyDemandZoneParams(StructureParams):
    """Configuration for the supply_demand_zone structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20


@dataclass
class SupplyDemandZoneRequest:
    data: Any
    params: SupplyDemandZoneParams = field(default_factory=SupplyDemandZoneParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SupplyDemandZoneReport = StructureReport


def normalize_input(request: SupplyDemandZoneRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: SupplyDemandZoneRequest) -> ModuleResult[SupplyDemandZoneReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SupplyDemandZoneParams", "SupplyDemandZoneRequest", "SupplyDemandZoneReport", "normalize_input", "run"]
