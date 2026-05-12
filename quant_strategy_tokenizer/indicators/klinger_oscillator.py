"""
quant_strategy_tokenizer.indicators.klinger_oscillator
=======================================================
Purpose: calculate a Klinger-style oscillator as an atomic flow token.
Core idea: Build a native volume-force approximation and compare fast and slow EMAs. Assumes volume force can expose longer-cycle accumulation shifts; use diagnostics for approximation notes.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, KlingerOscillatorParams, and ModuleRunContext.
Outputs: KlingerOscillatorReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'klinger_oscillator'
INPUT_KIND = 'ohlcv'


@dataclass
class KlingerOscillatorParams(VolumeParams):
    """Configuration for the klinger_oscillator volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    fast_window: int = 34
    slow_window: int = 55
    signal_window: int = 13


@dataclass
class KlingerOscillatorRequest:
    data: Any
    params: KlingerOscillatorParams = field(default_factory=KlingerOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


KlingerOscillatorReport = VolumeReport


def normalize_input(request: KlingerOscillatorRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: KlingerOscillatorRequest) -> ModuleResult[KlingerOscillatorReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["KlingerOscillatorParams", "KlingerOscillatorRequest", "KlingerOscillatorReport", "normalize_input", "run"]
