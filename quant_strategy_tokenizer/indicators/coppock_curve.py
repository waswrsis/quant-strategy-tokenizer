"""
quant_strategy_tokenizer.indicators.coppock_curve
=================================================
Purpose: Coppock Curve long-horizon momentum token.
Core idea: Add two longer ROC series and smooth the sum with a weighted moving average. The implementation assumes longer-term momentum turns become clearer after WMA smoothing.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, CoppockCurveParams, and ModuleRunContext.
Outputs: CoppockCurveReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'coppock_curve'
INPUT_KIND = 'price'


@dataclass
class CoppockCurveParams(MomentumParams):
    """Configuration for the coppock_curve momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    short_window: int = 11
    long_window: int = 14
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class CoppockCurveRequest:
    data: Any
    params: CoppockCurveParams = field(default_factory=CoppockCurveParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


CoppockCurveReport = MomentumReport


def normalize_input(request: CoppockCurveRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: CoppockCurveRequest) -> ModuleResult[CoppockCurveReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["CoppockCurveParams", "CoppockCurveRequest", "CoppockCurveReport", "normalize_input", "run"]
