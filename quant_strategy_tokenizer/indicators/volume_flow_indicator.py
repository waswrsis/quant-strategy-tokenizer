"""
quant_strategy_tokenizer.indicators.volume_flow_indicator
==========================================================
Purpose: calculate a volume flow indicator as an atomic pressure token.
Core idea: Sum signed volume by typical-price direction and normalize by average volume. Assumes persistent signed participation reveals flow pressure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeFlowIndicatorParams, and ModuleRunContext.
Outputs: VolumeFlowIndicatorReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_flow_indicator'
INPUT_KIND = 'ohlcv'


@dataclass
class VolumeFlowIndicatorParams(VolumeParams):
    """Configuration for the volume_flow_indicator volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 30


@dataclass
class VolumeFlowIndicatorRequest:
    data: Any
    params: VolumeFlowIndicatorParams = field(default_factory=VolumeFlowIndicatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeFlowIndicatorReport = VolumeReport


def normalize_input(request: VolumeFlowIndicatorRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeFlowIndicatorRequest) -> ModuleResult[VolumeFlowIndicatorReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeFlowIndicatorParams", "VolumeFlowIndicatorRequest", "VolumeFlowIndicatorReport", "normalize_input", "run"]
