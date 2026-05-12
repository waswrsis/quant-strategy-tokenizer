"""
quant_strategy_tokenizer.indicators.obv
========================================
Purpose: calculate On-Balance Volume as an atomic accumulation token.
Core idea: Accumulate signed volume using close-to-close price direction. Assumes volume on up closes reflects accumulation and volume on down closes reflects distribution.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, OBVParams, and ModuleRunContext.
Outputs: OBVReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'obv'
INPUT_KIND = 'price_volume'


@dataclass
class OBVParams(VolumeParams):
    """Configuration for the obv volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class OBVRequest:
    data: Any
    params: OBVParams = field(default_factory=OBVParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


OBVReport = VolumeReport


def normalize_input(request: OBVRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: OBVRequest) -> ModuleResult[OBVReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["OBVParams", "OBVRequest", "OBVReport", "normalize_input", "run"]
