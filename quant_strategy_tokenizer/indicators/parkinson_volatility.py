"""
quant_strategy_tokenizer.indicators.parkinson_volatility
=========================================================
Purpose: calculate Parkinson high-low volatility as an atomic volatility token.
Core idea: Use squared log high-low range to estimate volatility. Assumes intrabar extremes improve efficiency when opening gaps are not central.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ParkinsonVolatilityParams, and ModuleRunContext.
Outputs: ParkinsonVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'parkinson_volatility'
INPUT_KIND = 'ohlc'


@dataclass
class ParkinsonVolatilityParams(VolatilityParams):
    """Configuration for the parkinson_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class ParkinsonVolatilityRequest:
    data: Any
    params: ParkinsonVolatilityParams = field(default_factory=ParkinsonVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ParkinsonVolatilityReport = VolatilityReport


def normalize_input(request: ParkinsonVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: ParkinsonVolatilityRequest) -> ModuleResult[ParkinsonVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ParkinsonVolatilityParams", "ParkinsonVolatilityRequest", "ParkinsonVolatilityReport", "normalize_input", "run"]
