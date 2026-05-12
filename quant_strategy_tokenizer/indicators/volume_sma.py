"""
quant_strategy_tokenizer.indicators.volume_sma
===============================================
Purpose: calculate a simple moving average of volume as an atomic volume token.
Core idea: Smooth raw volume with a rolling arithmetic mean. Assumes average participation is a useful local baseline for filters and comparisons.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeSMAParams, and ModuleRunContext.
Outputs: VolumeSMAReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_sma'
INPUT_KIND = 'volume'


@dataclass
class VolumeSMAParams(VolumeParams):
    """Configuration for the volume_sma volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class VolumeSMARequest:
    data: Any
    params: VolumeSMAParams = field(default_factory=VolumeSMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeSMAReport = VolumeReport


def normalize_input(request: VolumeSMARequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeSMARequest) -> ModuleResult[VolumeSMAReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeSMAParams", "VolumeSMARequest", "VolumeSMAReport", "normalize_input", "run"]
