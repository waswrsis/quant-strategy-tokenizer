"""
quant_strategy_tokenizer.indicators.volume_spike
=================================================
Purpose: detect abnormal volume expansion as an atomic volume token.
Core idea: Compare current volume to a prior rolling average and flag ratios above spike_multiplier. Assumes sudden activity expansion can validate or invalidate signals.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeSpikeParams, and ModuleRunContext.
Outputs: VolumeSpikeReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_spike'
INPUT_KIND = 'volume'


@dataclass
class VolumeSpikeParams(VolumeParams):
    """Configuration for the volume_spike volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    spike_multiplier: float = 2.5


@dataclass
class VolumeSpikeRequest:
    data: Any
    params: VolumeSpikeParams = field(default_factory=VolumeSpikeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeSpikeReport = VolumeReport


def normalize_input(request: VolumeSpikeRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeSpikeRequest) -> ModuleResult[VolumeSpikeReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeSpikeParams", "VolumeSpikeRequest", "VolumeSpikeReport", "normalize_input", "run"]
