"""
quant_strategy_tokenizer.indicators.volume_percentile
======================================================
Purpose: rank volume inside a rolling history as an atomic regime token.
Core idea: Compute the latest volume percentile inside a rolling regime window. Assumes percentile context is more portable across assets than fixed volume thresholds.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumePercentileParams, and ModuleRunContext.
Outputs: VolumePercentileReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_percentile'
INPUT_KIND = 'volume'


@dataclass
class VolumePercentileParams(VolumeParams):
    """Configuration for the volume_percentile volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    regime_window: int = 100


@dataclass
class VolumePercentileRequest:
    data: Any
    params: VolumePercentileParams = field(default_factory=VolumePercentileParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumePercentileReport = VolumeReport


def normalize_input(request: VolumePercentileRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumePercentileRequest) -> ModuleResult[VolumePercentileReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumePercentileParams", "VolumePercentileRequest", "VolumePercentileReport", "normalize_input", "run"]
