"""
quant_strategy_tokenizer.indicators.equal_highs_lows
=====================================================
Purpose: detect equal highs and lows as an atomic structure token.
Core idea: Compare current extremes to recent rolling extremes within tolerance_pct. Assumes clustered equal highs/lows can mark visible liquidity pools.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, EqualHighsLowsParams, and ModuleRunContext.
Outputs: EqualHighsLowsReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'equal_highs_lows'
INPUT_KIND = 'ohlc'


@dataclass
class EqualHighsLowsParams(StructureParams):
    """Configuration for the equal_highs_lows structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    tolerance_pct: float = 0.003


@dataclass
class EqualHighsLowsRequest:
    data: Any
    params: EqualHighsLowsParams = field(default_factory=EqualHighsLowsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


EqualHighsLowsReport = StructureReport


def normalize_input(request: EqualHighsLowsRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: EqualHighsLowsRequest) -> ModuleResult[EqualHighsLowsReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["EqualHighsLowsParams", "EqualHighsLowsRequest", "EqualHighsLowsReport", "normalize_input", "run"]
