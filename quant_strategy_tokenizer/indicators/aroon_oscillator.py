"""
quant_strategy_tokenizer.indicators.aroon_oscillator
====================================================
Module purpose: Aroon oscillator trend-recency token.
Core idea: Compute Aroon Up minus Aroon Down. The implementation assumes the distance between recent-high recency and recent-low recency is a compact trend-direction measure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, AroonOscillatorParams, and ModuleRunContext.
Outputs: AroonOscillatorReport with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'aroon_oscillator'
INPUT_KIND = 'ohlc'


@dataclass
class AroonOscillatorParams(TrendParams):
    """Configuration for the aroon_oscillator trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 25


@dataclass
class AroonOscillatorRequest:
    data: Any
    params: AroonOscillatorParams = field(default_factory=AroonOscillatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AroonOscillatorReport = TrendReport


def normalize_input(request: AroonOscillatorRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: AroonOscillatorRequest) -> ModuleResult[AroonOscillatorReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AroonOscillatorParams", "AroonOscillatorRequest", "AroonOscillatorReport", "normalize_input", "run"]
