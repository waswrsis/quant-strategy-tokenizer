"""
quant_strategy_tokenizer.indicators.value_area
===============================================
Purpose: estimate value area from OHLCV profile as an atomic structure token.
Core idea: Select bins that accumulate value_area_pct of approximate profile volume. Assumes binned close-volume profile is acceptable for coarse structure work.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ValueAreaParams, and ModuleRunContext.
Outputs: ValueAreaReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'value_area'
INPUT_KIND = 'ohlcv'


@dataclass
class ValueAreaParams(StructureParams):
    """Configuration for the value_area structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    lookback: int = 120
    profile_bins: int = 24
    value_area_pct: float = 70.0


@dataclass
class ValueAreaRequest:
    data: Any
    params: ValueAreaParams = field(default_factory=ValueAreaParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ValueAreaReport = StructureReport


def normalize_input(request: ValueAreaRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: ValueAreaRequest) -> ModuleResult[ValueAreaReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ValueAreaParams", "ValueAreaRequest", "ValueAreaReport", "normalize_input", "run"]
