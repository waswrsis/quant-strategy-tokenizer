"""
quant_strategy_tokenizer.indicators.rogers_satchell_volatility
===============================================================
Purpose: calculate Rogers-Satchell OHLC volatility as an atomic volatility token.
Core idea: Use directional high/open/close and low/open/close log products. Assumes the estimator is useful when drift may be present.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RogersSatchellVolatilityParams, and ModuleRunContext.
Outputs: RogersSatchellVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'rogers_satchell_volatility'
INPUT_KIND = 'ohlc_open'


@dataclass
class RogersSatchellVolatilityParams(VolatilityParams):
    """Configuration for the rogers_satchell_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RogersSatchellVolatilityRequest:
    data: Any
    params: RogersSatchellVolatilityParams = field(default_factory=RogersSatchellVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RogersSatchellVolatilityReport = VolatilityReport


def normalize_input(request: RogersSatchellVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RogersSatchellVolatilityRequest) -> ModuleResult[RogersSatchellVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RogersSatchellVolatilityParams", "RogersSatchellVolatilityRequest", "RogersSatchellVolatilityReport", "normalize_input", "run"]
