"""
quant_strategy_tokenizer.indicators.downside_volatility
========================================================
Purpose: calculate downside-only return volatility as an atomic volatility token.
Core idea: Square and average only negative log returns. Assumes harmful volatility is asymmetric and downside moves deserve separate measurement.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, DownsideVolatilityParams, and ModuleRunContext.
Outputs: DownsideVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'downside_volatility'
INPUT_KIND = 'price'


@dataclass
class DownsideVolatilityParams(VolatilityParams):
    """Configuration for the downside_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class DownsideVolatilityRequest:
    data: Any
    params: DownsideVolatilityParams = field(default_factory=DownsideVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DownsideVolatilityReport = VolatilityReport


def normalize_input(request: DownsideVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: DownsideVolatilityRequest) -> ModuleResult[DownsideVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DownsideVolatilityParams", "DownsideVolatilityRequest", "DownsideVolatilityReport", "normalize_input", "run"]
