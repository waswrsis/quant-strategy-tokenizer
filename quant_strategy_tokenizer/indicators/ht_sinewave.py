"""
quant_strategy_tokenizer.indicators.ht_sinewave
===============================================
Purpose: Hilbert transform sinewave token.
Core idea: Compute sine and lead-sine cycle components using TA-Lib or a native phase approximation. The implementation assumes cycle phase can help identify turns; native mode is approximate and diagnostic rather than exact.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, HTSineWaveParams, and ModuleRunContext.
Outputs: HTSineWaveReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ht_sinewave'
INPUT_KIND = 'price'


@dataclass
class HTSineWaveParams(TrendParams):
    """Configuration for the ht_sinewave trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    cycle_window: int = 32


@dataclass
class HTSineWaveRequest:
    data: Any
    params: HTSineWaveParams = field(default_factory=HTSineWaveParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HTSineWaveReport = TrendReport


def normalize_input(request: HTSineWaveRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: HTSineWaveRequest) -> ModuleResult[HTSineWaveReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["HTSineWaveParams", "HTSineWaveRequest", "HTSineWaveReport", "normalize_input", "run"]
