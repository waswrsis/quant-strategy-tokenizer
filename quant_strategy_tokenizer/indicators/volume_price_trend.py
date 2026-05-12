"""
quant_strategy_tokenizer.indicators.volume_price_trend
=======================================================
Purpose: calculate Volume Price Trend as an atomic flow token.
Core idea: Accumulate volume weighted by close-to-close percentage change. Assumes larger volume should amplify price-change pressure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumePriceTrendParams, and ModuleRunContext.
Outputs: VolumePriceTrendReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_price_trend'
INPUT_KIND = 'price_volume'


@dataclass
class VolumePriceTrendParams(VolumeParams):
    """Configuration for the volume_price_trend volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class VolumePriceTrendRequest:
    data: Any
    params: VolumePriceTrendParams = field(default_factory=VolumePriceTrendParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumePriceTrendReport = VolumeReport


def normalize_input(request: VolumePriceTrendRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumePriceTrendRequest) -> ModuleResult[VolumePriceTrendReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumePriceTrendParams", "VolumePriceTrendRequest", "VolumePriceTrendReport", "normalize_input", "run"]
