"""
quant_strategy_tokenizer.indicators.accumulation_distribution_line
===================================================================
Purpose: calculate Accumulation/Distribution Line as an atomic flow token.
Core idea: Accumulate close-location-value multiplied by volume. Assumes where price closes inside the bar range approximates buying or selling pressure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, AccumulationDistributionLineParams, and ModuleRunContext.
Outputs: AccumulationDistributionLineReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'accumulation_distribution_line'
INPUT_KIND = 'ohlcv'


@dataclass
class AccumulationDistributionLineParams(VolumeParams):
    """Configuration for the accumulation_distribution_line volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class AccumulationDistributionLineRequest:
    data: Any
    params: AccumulationDistributionLineParams = field(default_factory=AccumulationDistributionLineParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AccumulationDistributionLineReport = VolumeReport


def normalize_input(request: AccumulationDistributionLineRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: AccumulationDistributionLineRequest) -> ModuleResult[AccumulationDistributionLineReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AccumulationDistributionLineParams", "AccumulationDistributionLineRequest", "AccumulationDistributionLineReport", "normalize_input", "run"]
