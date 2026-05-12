"""
quant_strategy_tokenizer.indicators.ppo
========================================
Module purpose: Percentage Price Oscillator trend-momentum token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, PPOParams, and ModuleRunContext.
Outputs: PPOReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ppo'
INPUT_KIND = 'price'


@dataclass
class PPOParams(TrendParams):
    """Configuration for the ppo trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    fast_window: int = 12
    slow_window: int = 26
    signal_window: int = 9


@dataclass
class PPORequest:
    data: Any
    params: PPOParams = field(default_factory=PPOParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PPOReport = TrendReport


def normalize_input(request: PPORequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: PPORequest) -> ModuleResult[PPOReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PPOParams", "PPORequest", "PPOReport", "normalize_input", "run"]
