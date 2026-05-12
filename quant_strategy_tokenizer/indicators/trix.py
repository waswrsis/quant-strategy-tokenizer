"""
quant_strategy_tokenizer.indicators.trix
========================================
Purpose: Triple-smoothed rate-of-change momentum token.
Core idea: Apply three EMA layers and calculate the one-period percent change of the triple-smoothed series. The implementation assumes triple smoothing filters noise before measuring momentum.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TRIXParams, and ModuleRunContext.
Outputs: TRIXReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'trix'
INPUT_KIND = 'price'


@dataclass
class TRIXParams(MomentumParams):
    """Configuration for the trix momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 15
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class TRIXRequest:
    data: Any
    params: TRIXParams = field(default_factory=TRIXParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TRIXReport = MomentumReport


def normalize_input(request: TRIXRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: TRIXRequest) -> ModuleResult[TRIXReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TRIXParams", "TRIXRequest", "TRIXReport", "normalize_input", "run"]
