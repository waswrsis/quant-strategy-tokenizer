"""
quant_strategy_tokenizer.indicators.price_volume_divergence
============================================================
Purpose: detect price-volume slope divergence as an atomic diagnostic token.
Core idea: Compare rolling price slope with rolling volume slope. Assumes trend quality weakens when price direction is not confirmed by participation.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PriceVolumeDivergenceParams, and ModuleRunContext.
Outputs: PriceVolumeDivergenceReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'price_volume_divergence'
INPUT_KIND = 'price_volume'


@dataclass
class PriceVolumeDivergenceParams(VolumeParams):
    """Configuration for the price_volume_divergence volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class PriceVolumeDivergenceRequest:
    data: Any
    params: PriceVolumeDivergenceParams = field(default_factory=PriceVolumeDivergenceParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PriceVolumeDivergenceReport = VolumeReport


def normalize_input(request: PriceVolumeDivergenceRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: PriceVolumeDivergenceRequest) -> ModuleResult[PriceVolumeDivergenceReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PriceVolumeDivergenceParams", "PriceVolumeDivergenceRequest", "PriceVolumeDivergenceReport", "normalize_input", "run"]
