"""
quant_strategy_tokenizer.indicators.ease_of_movement
=====================================================
Purpose: calculate Ease of Movement as an atomic liquidity-pressure token.
Core idea: Relate midpoint movement and range to volume. Assumes large price movement on low volume means easier movement, while high volume dampens it.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, EaseOfMovementParams, and ModuleRunContext.
Outputs: EaseOfMovementReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'ease_of_movement'
INPUT_KIND = 'ohlcv'


@dataclass
class EaseOfMovementParams(VolumeParams):
    """Configuration for the ease_of_movement volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 14


@dataclass
class EaseOfMovementRequest:
    data: Any
    params: EaseOfMovementParams = field(default_factory=EaseOfMovementParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


EaseOfMovementReport = VolumeReport


def normalize_input(request: EaseOfMovementRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: EaseOfMovementRequest) -> ModuleResult[EaseOfMovementReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["EaseOfMovementParams", "EaseOfMovementRequest", "EaseOfMovementReport", "normalize_input", "run"]
