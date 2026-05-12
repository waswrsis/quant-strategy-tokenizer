"""
quant_strategy_tokenizer.indicators.bollinger_bands
====================================================
Purpose: calculate Bollinger band width and levels as an atomic volatility token.
Core idea: Build moving-average bands at configurable standard-deviation distance. Assumes band width and percent-b reveal volatility expansion and price location.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, BollingerBandsParams, and ModuleRunContext.
Outputs: BollingerBandsReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'bollinger_bands'
INPUT_KIND = 'price'


@dataclass
class BollingerBandsParams(VolatilityParams):
    """Configuration for the bollinger_bands volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    stddev_multiplier: float = 2.0


@dataclass
class BollingerBandsRequest:
    data: Any
    params: BollingerBandsParams = field(default_factory=BollingerBandsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BollingerBandsReport = VolatilityReport


def normalize_input(request: BollingerBandsRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: BollingerBandsRequest) -> ModuleResult[BollingerBandsReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["BollingerBandsParams", "BollingerBandsRequest", "BollingerBandsReport", "normalize_input", "run"]
