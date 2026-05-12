"""
quant_strategy_tokenizer.indicators.zscore_bands
=================================================
Purpose: calculate z-score bands and standardized deviation as an atomic volatility token.
Core idea: Return z-score plus mean and standard-deviation bands. Assumes users may want both normalized deviation and raw band levels.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ZScoreBandsParams, and ModuleRunContext.
Outputs: ZScoreBandsReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'zscore_bands'
INPUT_KIND = 'price'


@dataclass
class ZScoreBandsParams(VolatilityParams):
    """Configuration for the zscore_bands volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    stddev_multiplier: float = 2.0


@dataclass
class ZScoreBandsRequest:
    data: Any
    params: ZScoreBandsParams = field(default_factory=ZScoreBandsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ZScoreBandsReport = VolatilityReport


def normalize_input(request: ZScoreBandsRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: ZScoreBandsRequest) -> ModuleResult[ZScoreBandsReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ZScoreBandsParams", "ZScoreBandsRequest", "ZScoreBandsReport", "normalize_input", "run"]
