"""
quant_strategy_tokenizer.indicators.relative_volume
====================================================
Purpose: calculate relative volume versus prior average as an atomic volume token.
Core idea: Divide current volume by a prior rolling volume baseline. Assumes current participation should be judged against recent normal activity, not absolute size.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RelativeVolumeParams, and ModuleRunContext.
Outputs: RelativeVolumeReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'relative_volume'
INPUT_KIND = 'volume'


@dataclass
class RelativeVolumeParams(VolumeParams):
    """Configuration for the relative_volume volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    spike_multiplier: float = 2.5


@dataclass
class RelativeVolumeRequest:
    data: Any
    params: RelativeVolumeParams = field(default_factory=RelativeVolumeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RelativeVolumeReport = VolumeReport


def normalize_input(request: RelativeVolumeRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: RelativeVolumeRequest) -> ModuleResult[RelativeVolumeReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RelativeVolumeParams", "RelativeVolumeRequest", "RelativeVolumeReport", "normalize_input", "run"]
