"""
quant_strategy_tokenizer.indicators.true_strength_index
=======================================================
Purpose: True Strength Index momentum token.
Core idea: Double-smooth price change and absolute price change, then divide them into a signed oscillator with a signal line. The implementation assumes smoothed directional change captures momentum persistence.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TrueStrengthIndexParams, and ModuleRunContext.
Outputs: TrueStrengthIndexReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'true_strength_index'
INPUT_KIND = 'price'


@dataclass
class TrueStrengthIndexParams(MomentumParams):
    """Configuration for the true_strength_index momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    fast_window: int = 13
    slow_window: int = 25
    signal_window: int = 13
    overbought: float = 25.0
    oversold: float = -25.0


@dataclass
class TrueStrengthIndexRequest:
    data: Any
    params: TrueStrengthIndexParams = field(default_factory=TrueStrengthIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TrueStrengthIndexReport = MomentumReport


def normalize_input(request: TrueStrengthIndexRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: TrueStrengthIndexRequest) -> ModuleResult[TrueStrengthIndexReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TrueStrengthIndexParams", "TrueStrengthIndexRequest", "TrueStrengthIndexReport", "normalize_input", "run"]
