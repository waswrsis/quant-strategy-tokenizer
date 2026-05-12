"""
quant_strategy_tokenizer.indicators.ht_dominant_cycle_phase
===========================================================
Purpose: Hilbert dominant cycle phase token.
Core idea: Estimate dominant cycle phase using TA-Lib or a native arctangent phase approximation. The implementation assumes detrended price and quadrature movement can represent cycle phase; native mode is approximate.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, HTDominantCyclePhaseParams, and ModuleRunContext.
Outputs: HTDominantCyclePhaseReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ht_dominant_cycle_phase'
INPUT_KIND = 'price'


@dataclass
class HTDominantCyclePhaseParams(TrendParams):
    """Configuration for the ht_dominant_cycle_phase trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    cycle_window: int = 48


@dataclass
class HTDominantCyclePhaseRequest:
    data: Any
    params: HTDominantCyclePhaseParams = field(default_factory=HTDominantCyclePhaseParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HTDominantCyclePhaseReport = TrendReport


def normalize_input(request: HTDominantCyclePhaseRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: HTDominantCyclePhaseRequest) -> ModuleResult[HTDominantCyclePhaseReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["HTDominantCyclePhaseParams", "HTDominantCyclePhaseRequest", "HTDominantCyclePhaseReport", "normalize_input", "run"]
