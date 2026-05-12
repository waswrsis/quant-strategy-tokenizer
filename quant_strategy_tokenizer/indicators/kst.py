"""
quant_strategy_tokenizer.indicators.kst
=======================================
Purpose: Know Sure Thing momentum token.
Core idea: Sum weighted smoothed ROC values across multiple horizons and compare with a signal line. The implementation assumes broad agreement across ROC horizons is stronger than a single-period momentum reading.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, KSTParams, and ModuleRunContext.
Outputs: KSTReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'kst'
INPUT_KIND = 'price'


@dataclass
class KSTParams(MomentumParams):
    """Configuration for the kst momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    short_window: int = 10
    medium_window: int = 15
    long_window: int = 30
    smooth_window: int = 10
    signal_window: int = 9
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class KSTRequest:
    data: Any
    params: KSTParams = field(default_factory=KSTParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


KSTReport = MomentumReport


def normalize_input(request: KSTRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: KSTRequest) -> ModuleResult[KSTReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["KSTParams", "KSTRequest", "KSTReport", "normalize_input", "run"]
