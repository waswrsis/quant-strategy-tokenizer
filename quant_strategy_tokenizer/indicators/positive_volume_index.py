"""
quant_strategy_tokenizer.indicators.positive_volume_index
==========================================================
Purpose: calculate Positive Volume Index as an atomic participation token.
Core idea: Update an index only on higher-volume bars. Assumes crowd participation appears more clearly when volume rises from the prior bar.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PositiveVolumeIndexParams, and ModuleRunContext.
Outputs: PositiveVolumeIndexReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'positive_volume_index'
INPUT_KIND = 'price_volume'


@dataclass
class PositiveVolumeIndexParams(VolumeParams):
    """Configuration for the positive_volume_index volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class PositiveVolumeIndexRequest:
    data: Any
    params: PositiveVolumeIndexParams = field(default_factory=PositiveVolumeIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PositiveVolumeIndexReport = VolumeReport


def normalize_input(request: PositiveVolumeIndexRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: PositiveVolumeIndexRequest) -> ModuleResult[PositiveVolumeIndexReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PositiveVolumeIndexParams", "PositiveVolumeIndexRequest", "PositiveVolumeIndexReport", "normalize_input", "run"]
