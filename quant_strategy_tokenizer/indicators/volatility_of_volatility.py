"""
quant_strategy_tokenizer.indicators.volatility_of_volatility
=============================================================
Purpose: calculate volatility-of-volatility as an atomic volatility token.
Core idea: Compute rolling standard deviation of historical volatility. Assumes instability in volatility itself is a distinct risk regime.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolatilityOfVolatilityParams, and ModuleRunContext.
Outputs: VolatilityOfVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'volatility_of_volatility'
INPUT_KIND = 'price'


@dataclass
class VolatilityOfVolatilityParams(VolatilityParams):
    """Configuration for the volatility_of_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    signal_window: int = 9


@dataclass
class VolatilityOfVolatilityRequest:
    data: Any
    params: VolatilityOfVolatilityParams = field(default_factory=VolatilityOfVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolatilityOfVolatilityReport = VolatilityReport


def normalize_input(request: VolatilityOfVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: VolatilityOfVolatilityRequest) -> ModuleResult[VolatilityOfVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolatilityOfVolatilityParams", "VolatilityOfVolatilityRequest", "VolatilityOfVolatilityReport", "normalize_input", "run"]
