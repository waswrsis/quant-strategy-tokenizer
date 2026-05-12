"""
quant_strategy_tokenizer.indicators.chaikin_oscillator
=======================================================
Purpose: calculate Chaikin Oscillator as an atomic flow-momentum token.
Core idea: Subtract slow EMA of ADL from fast EMA of ADL. Assumes shifts in accumulation/distribution momentum can lead price behavior.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ChaikinOscillatorParams, and ModuleRunContext.
Outputs: ChaikinOscillatorReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'chaikin_oscillator'
INPUT_KIND = 'ohlcv'


@dataclass
class ChaikinOscillatorParams(VolumeParams):
    """Configuration for the chaikin_oscillator volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    fast_window: int = 3
    slow_window: int = 10


@dataclass
class ChaikinOscillatorRequest:
    data: Any
    params: ChaikinOscillatorParams = field(default_factory=ChaikinOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ChaikinOscillatorReport = VolumeReport


def normalize_input(request: ChaikinOscillatorRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: ChaikinOscillatorRequest) -> ModuleResult[ChaikinOscillatorReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ChaikinOscillatorParams", "ChaikinOscillatorRequest", "ChaikinOscillatorReport", "normalize_input", "run"]
