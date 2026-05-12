"""
quant_strategy_tokenizer.indicators.ewma_volatility
====================================================
Purpose: calculate exponentially weighted return volatility as an atomic volatility token.
Core idea: Apply an EWMA decay to squared log returns. Assumes recent shocks should receive more weight than older observations.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, EWMAVolatilityParams, and ModuleRunContext.
Outputs: EWMAVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'ewma_volatility'
INPUT_KIND = 'price'


@dataclass
class EWMAVolatilityParams(VolatilityParams):
    """Configuration for the ewma_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    ewma_lambda: float = 0.94


@dataclass
class EWMAVolatilityRequest:
    data: Any
    params: EWMAVolatilityParams = field(default_factory=EWMAVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


EWMAVolatilityReport = VolatilityReport


def normalize_input(request: EWMAVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: EWMAVolatilityRequest) -> ModuleResult[EWMAVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["EWMAVolatilityParams", "EWMAVolatilityRequest", "EWMAVolatilityReport", "normalize_input", "run"]
