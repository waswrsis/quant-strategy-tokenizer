"""
quant_strategy_tokenizer.indicators.point_of_control
=====================================================
Purpose: estimate point of control from OHLCV profile as an atomic structure token.
Core idea: Select the highest-volume close-price bin. Assumes binned OHLCV close and volume can approximate POC when tick profile is unavailable.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PointOfControlParams, and ModuleRunContext.
Outputs: PointOfControlReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'point_of_control'
INPUT_KIND = 'ohlcv'


@dataclass
class PointOfControlParams(StructureParams):
    """Configuration for the point_of_control structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    lookback: int = 120
    profile_bins: int = 24


@dataclass
class PointOfControlRequest:
    data: Any
    params: PointOfControlParams = field(default_factory=PointOfControlParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PointOfControlReport = StructureReport


def normalize_input(request: PointOfControlRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: PointOfControlRequest) -> ModuleResult[PointOfControlReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PointOfControlParams", "PointOfControlRequest", "PointOfControlReport", "normalize_input", "run"]
