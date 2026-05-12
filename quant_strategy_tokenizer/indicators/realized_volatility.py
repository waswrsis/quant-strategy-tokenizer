"""
quant_strategy_tokenizer.indicators.realized_volatility
========================================================
Purpose: calculate realized volatility from squared log returns as an atomic volatility token.
Core idea: Sum squared log returns over the lookback and square-root the result. Assumes realized variance captures path volatility over the window.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RealizedVolatilityParams, and ModuleRunContext.
Outputs: RealizedVolatilityReport with quality, last values, volatility direction, volatility
level, signal, regime, optional series, input profile, used fields, warnings,
and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
unavailable requested backend, or invalid zero-denominator calculations return
ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .volatility_common import VolatilityParams, VolatilityReport, normalize_volatility_input, run_volatility_indicator


INDICATOR = 'realized_volatility'
INPUT_KIND = 'price'


@dataclass
class RealizedVolatilityParams(VolatilityParams):
    """Configuration for the realized_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RealizedVolatilityRequest:
    data: Any
    params: RealizedVolatilityParams = field(default_factory=RealizedVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RealizedVolatilityReport = VolatilityReport


def normalize_input(request: RealizedVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RealizedVolatilityRequest) -> ModuleResult[RealizedVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RealizedVolatilityParams", "RealizedVolatilityRequest", "RealizedVolatilityReport", "normalize_input", "run"]
