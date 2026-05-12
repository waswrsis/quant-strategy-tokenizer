"""
quant_strategy_tokenizer.indicators.volume_oscillator
======================================================
Purpose: calculate a fast-slow volume oscillator as an atomic volume token.
Core idea: Compare fast and slow EMA volume baselines. Assumes participation momentum can be represented by the spread between short and long volume averages.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeOscillatorParams, and ModuleRunContext.
Outputs: VolumeOscillatorReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_oscillator'
INPUT_KIND = 'volume'


@dataclass
class VolumeOscillatorParams(VolumeParams):
    """Configuration for the volume_oscillator volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    fast_window: int = 10
    slow_window: int = 20


@dataclass
class VolumeOscillatorRequest:
    data: Any
    params: VolumeOscillatorParams = field(default_factory=VolumeOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeOscillatorReport = VolumeReport


def normalize_input(request: VolumeOscillatorRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeOscillatorRequest) -> ModuleResult[VolumeOscillatorReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeOscillatorParams", "VolumeOscillatorRequest", "VolumeOscillatorReport", "normalize_input", "run"]
