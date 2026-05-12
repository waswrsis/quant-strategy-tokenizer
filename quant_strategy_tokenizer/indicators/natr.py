"""
quant_strategy_tokenizer.indicators.natr
=========================================
Purpose: calculate Normalized Average True Range as an atomic volatility token.
Core idea: Smooth true range with Wilder-style ATR and divide by close price. Assumes volatility should be comparable across instruments after price normalization.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, NATRParams, and ModuleRunContext.
Outputs: NATRReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'natr'
INPUT_KIND = 'ohlc'


@dataclass
class NATRParams(VolatilityParams):
    """Configuration for the natr volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 14


@dataclass
class NATRRequest:
    data: Any
    params: NATRParams = field(default_factory=NATRParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NATRReport = VolatilityReport


def normalize_input(request: NATRRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: NATRRequest) -> ModuleResult[NATRReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["NATRParams", "NATRRequest", "NATRReport", "normalize_input", "run"]
