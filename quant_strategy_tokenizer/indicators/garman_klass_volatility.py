"""
quant_strategy_tokenizer.indicators.garman_klass_volatility
============================================================
Purpose: calculate Garman-Klass OHLC volatility as an atomic volatility token.
Core idea: Combine log high-low and close-open terms. Assumes OHLC information improves volatility estimation under limited drift.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, GarmanKlassVolatilityParams, and ModuleRunContext.
Outputs: GarmanKlassVolatilityReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'garman_klass_volatility'
INPUT_KIND = 'ohlc_open'


@dataclass
class GarmanKlassVolatilityParams(VolatilityParams):
    """Configuration for the garman_klass_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class GarmanKlassVolatilityRequest:
    data: Any
    params: GarmanKlassVolatilityParams = field(default_factory=GarmanKlassVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


GarmanKlassVolatilityReport = VolatilityReport


def normalize_input(request: GarmanKlassVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: GarmanKlassVolatilityRequest) -> ModuleResult[GarmanKlassVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["GarmanKlassVolatilityParams", "GarmanKlassVolatilityRequest", "GarmanKlassVolatilityReport", "normalize_input", "run"]
