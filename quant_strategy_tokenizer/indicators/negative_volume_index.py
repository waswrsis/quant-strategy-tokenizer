"""
quant_strategy_tokenizer.indicators.negative_volume_index
==========================================================
Purpose: calculate Negative Volume Index as an atomic participation token.
Core idea: Update an index only on lower-volume bars. Assumes informed or quieter participation may appear when volume contracts.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, NegativeVolumeIndexParams, and ModuleRunContext.
Outputs: NegativeVolumeIndexReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'negative_volume_index'
INPUT_KIND = 'price_volume'


@dataclass
class NegativeVolumeIndexParams(VolumeParams):
    """Configuration for the negative_volume_index volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class NegativeVolumeIndexRequest:
    data: Any
    params: NegativeVolumeIndexParams = field(default_factory=NegativeVolumeIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NegativeVolumeIndexReport = VolumeReport


def normalize_input(request: NegativeVolumeIndexRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: NegativeVolumeIndexRequest) -> ModuleResult[NegativeVolumeIndexReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["NegativeVolumeIndexParams", "NegativeVolumeIndexRequest", "NegativeVolumeIndexReport", "normalize_input", "run"]
