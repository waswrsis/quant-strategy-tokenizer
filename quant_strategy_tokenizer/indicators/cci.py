"""
quant_strategy_tokenizer.indicators.cci
=======================================
Purpose: Commodity Channel Index momentum token.
Core idea: Compare typical price with its rolling mean scaled by mean absolute deviation. The implementation assumes unusually large deviations from a local typical-price mean identify momentum extremes.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, CCIParams, and ModuleRunContext.
Outputs: CCIReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'cci'
INPUT_KIND = 'ohlc'


@dataclass
class CCIParams(MomentumParams):
    """Configuration for the cci momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 20
    cci_constant: float = 0.015
    overbought: float = 100.0
    oversold: float = -100.0


@dataclass
class CCIRequest:
    data: Any
    params: CCIParams = field(default_factory=CCIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


CCIReport = MomentumReport


def normalize_input(request: CCIRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: CCIRequest) -> ModuleResult[CCIReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["CCIParams", "CCIRequest", "CCIReport", "normalize_input", "run"]
