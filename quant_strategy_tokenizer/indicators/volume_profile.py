"""
quant_strategy_tokenizer.indicators.volume_profile
===================================================
Purpose: approximate volume profile from OHLCV as an atomic structure token.
Core idea: Bin close prices by volume over lookback. Assumes close-price binning is only an approximation of real volume profile without tick data.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeProfileParams, and ModuleRunContext.
Outputs: VolumeProfileReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'volume_profile'
INPUT_KIND = 'ohlcv'


@dataclass
class VolumeProfileParams(StructureParams):
    """Configuration for the volume_profile structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    lookback: int = 120
    profile_bins: int = 24


@dataclass
class VolumeProfileRequest:
    data: Any
    params: VolumeProfileParams = field(default_factory=VolumeProfileParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeProfileReport = StructureReport


def normalize_input(request: VolumeProfileRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: VolumeProfileRequest) -> ModuleResult[VolumeProfileReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeProfileParams", "VolumeProfileRequest", "VolumeProfileReport", "normalize_input", "run"]
