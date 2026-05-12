"""
quant_strategy_tokenizer.indicators.rolling_support_resistance
===============================================================
Purpose: cluster rolling swing support and resistance as an atomic token.
Core idea: Cluster recent swing highs and lows by tolerance_pct. Assumes repeated nearby extrema form more meaningful levels than isolated prices.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RollingSupportResistanceParams, and ModuleRunContext.
Outputs: RollingSupportResistanceReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'rolling_support_resistance'
INPUT_KIND = 'ohlc'


@dataclass
class RollingSupportResistanceParams(StructureParams):
    """Configuration for the rolling_support_resistance structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    min_touches: int = 2
    max_levels: int = 8


@dataclass
class RollingSupportResistanceRequest:
    data: Any
    params: RollingSupportResistanceParams = field(default_factory=RollingSupportResistanceParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RollingSupportResistanceReport = StructureReport


def normalize_input(request: RollingSupportResistanceRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: RollingSupportResistanceRequest) -> ModuleResult[RollingSupportResistanceReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RollingSupportResistanceParams", "RollingSupportResistanceRequest", "RollingSupportResistanceReport", "normalize_input", "run"]
