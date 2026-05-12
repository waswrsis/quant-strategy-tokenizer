"""
quant_strategy_tokenizer.indicators.volume_dry_up
==================================================
Purpose: detect volume dry-up as an atomic volume token.
Core idea: Rank volume inside a rolling window and flag low-percentile activity. Assumes quiet participation can mark compression, weak confirmation, or liquidity risk.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeDryUpParams, and ModuleRunContext.
Outputs: VolumeDryUpReport with quality, last values, volume direction, volume level,
flow direction, signal, regime, optional series, input profile, used fields,
warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, all-zero volume,
insufficient history, unavailable requested backend, or invalid zero-denominator
calculations return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .volume_common import VolumeParams, VolumeReport, normalize_volume_input, run_volume_indicator


INDICATOR = 'volume_dry_up'
INPUT_KIND = 'volume'


@dataclass
class VolumeDryUpParams(VolumeParams):
    """Configuration for the volume_dry_up volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    regime_window: int = 100
    dry_up_percentile: float = 20.0


@dataclass
class VolumeDryUpRequest:
    data: Any
    params: VolumeDryUpParams = field(default_factory=VolumeDryUpParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeDryUpReport = VolumeReport


def normalize_input(request: VolumeDryUpRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeDryUpRequest) -> ModuleResult[VolumeDryUpReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeDryUpParams", "VolumeDryUpRequest", "VolumeDryUpReport", "normalize_input", "run"]
