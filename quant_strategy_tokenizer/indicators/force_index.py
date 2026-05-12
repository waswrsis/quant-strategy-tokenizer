"""
quant_strategy_tokenizer.indicators.force_index
================================================
Purpose: calculate Elder Force Index as an atomic pressure token.
Core idea: Multiply close change by volume and smooth it. Assumes price movement with volume represents directional force.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ForceIndexParams, and ModuleRunContext.
Outputs: ForceIndexReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'force_index'
INPUT_KIND = 'price_volume'


@dataclass
class ForceIndexParams(VolumeParams):
    """Configuration for the force_index volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 13


@dataclass
class ForceIndexRequest:
    data: Any
    params: ForceIndexParams = field(default_factory=ForceIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ForceIndexReport = VolumeReport


def normalize_input(request: ForceIndexRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: ForceIndexRequest) -> ModuleResult[ForceIndexReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ForceIndexParams", "ForceIndexRequest", "ForceIndexReport", "normalize_input", "run"]
