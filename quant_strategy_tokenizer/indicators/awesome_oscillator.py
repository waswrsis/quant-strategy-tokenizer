"""
quant_strategy_tokenizer.indicators.awesome_oscillator
======================================================
Purpose: Awesome Oscillator median-price momentum token.
Core idea: Subtract a slow SMA of median price from a fast SMA of median price. The implementation assumes the fast/slow median-price spread captures short-term momentum against a longer baseline.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, AwesomeOscillatorParams, and ModuleRunContext.
Outputs: AwesomeOscillatorReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'awesome_oscillator'
INPUT_KIND = 'ohlc'


@dataclass
class AwesomeOscillatorParams(MomentumParams):
    """Configuration for the awesome_oscillator momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    fast_window: int = 5
    slow_window: int = 34
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class AwesomeOscillatorRequest:
    data: Any
    params: AwesomeOscillatorParams = field(default_factory=AwesomeOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AwesomeOscillatorReport = MomentumReport


def normalize_input(request: AwesomeOscillatorRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: AwesomeOscillatorRequest) -> ModuleResult[AwesomeOscillatorReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AwesomeOscillatorParams", "AwesomeOscillatorRequest", "AwesomeOscillatorReport", "normalize_input", "run"]
