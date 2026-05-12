"""
quant_strategy_tokenizer.indicators.accelerator_oscillator
==========================================================
Purpose: Acceleration/Deceleration Oscillator token.
Core idea: Subtract a short moving average of Awesome Oscillator from the Awesome Oscillator itself. The implementation assumes acceleration changes before raw momentum crosses zero.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, AcceleratorOscillatorParams, and ModuleRunContext.
Outputs: AcceleratorOscillatorReport with quality, last values, momentum direction, signal,
zone, optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .momentum_common import MomentumParams, MomentumReport, normalize_momentum_input, run_momentum_indicator


INDICATOR = 'accelerator_oscillator'
INPUT_KIND = 'ohlc'


@dataclass
class AcceleratorOscillatorParams(MomentumParams):
    """Configuration for the accelerator_oscillator momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    fast_window: int = 5
    slow_window: int = 34
    signal_window: int = 5
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class AcceleratorOscillatorRequest:
    data: Any
    params: AcceleratorOscillatorParams = field(default_factory=AcceleratorOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AcceleratorOscillatorReport = MomentumReport


def normalize_input(request: AcceleratorOscillatorRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: AcceleratorOscillatorRequest) -> ModuleResult[AcceleratorOscillatorReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AcceleratorOscillatorParams", "AcceleratorOscillatorRequest", "AcceleratorOscillatorReport", "normalize_input", "run"]
