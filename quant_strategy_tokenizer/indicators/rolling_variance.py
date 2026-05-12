"""
quant_strategy_tokenizer.indicators.rolling_variance
=====================================================
Purpose: calculate rolling variance of log returns as an atomic volatility token.
Core idea: Apply rolling variance to log returns. Assumes squared dispersion is useful for models that operate on variance rather than volatility.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RollingVarianceParams, and ModuleRunContext.
Outputs: RollingVarianceReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'rolling_variance'
INPUT_KIND = 'price'


@dataclass
class RollingVarianceParams(VolatilityParams):
    """Configuration for the rolling_variance volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RollingVarianceRequest:
    data: Any
    params: RollingVarianceParams = field(default_factory=RollingVarianceParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RollingVarianceReport = VolatilityReport


def normalize_input(request: RollingVarianceRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RollingVarianceRequest) -> ModuleResult[RollingVarianceReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RollingVarianceParams", "RollingVarianceRequest", "RollingVarianceReport", "normalize_input", "run"]
