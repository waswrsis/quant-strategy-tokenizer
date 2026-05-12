"""
quant_strategy_tokenizer.indicators.ultimate_oscillator
=======================================================
Purpose: Ultimate Oscillator multi-horizon momentum token.
Core idea: Combine buying pressure divided by true range across short, medium, and long windows. The implementation assumes multi-horizon confirmation reduces false momentum signals from a single lookback.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, UltimateOscillatorParams, and ModuleRunContext.
Outputs: UltimateOscillatorReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'ultimate_oscillator'
INPUT_KIND = 'ohlc'


@dataclass
class UltimateOscillatorParams(MomentumParams):
    """Configuration for the ultimate_oscillator momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    short_window: int = 7
    medium_window: int = 14
    long_window: int = 28
    overbought: float = 70.0
    oversold: float = 30.0


@dataclass
class UltimateOscillatorRequest:
    data: Any
    params: UltimateOscillatorParams = field(default_factory=UltimateOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


UltimateOscillatorReport = MomentumReport


def normalize_input(request: UltimateOscillatorRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: UltimateOscillatorRequest) -> ModuleResult[UltimateOscillatorReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["UltimateOscillatorParams", "UltimateOscillatorRequest", "UltimateOscillatorReport", "normalize_input", "run"]
