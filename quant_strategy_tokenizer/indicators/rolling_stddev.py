"""
quant_strategy_tokenizer.indicators.rolling_stddev
===================================================
Purpose: calculate rolling standard deviation of log returns as an atomic volatility token.
Core idea: Apply rolling standard deviation to log returns. Assumes close-to-close return dispersion is the baseline statistical volatility measure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RollingStddevParams, and ModuleRunContext.
Outputs: RollingStddevReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'rolling_stddev'
INPUT_KIND = 'price'


@dataclass
class RollingStddevParams(VolatilityParams):
    """Configuration for the rolling_stddev volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RollingStddevRequest:
    data: Any
    params: RollingStddevParams = field(default_factory=RollingStddevParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RollingStddevReport = VolatilityReport


def normalize_input(request: RollingStddevRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RollingStddevRequest) -> ModuleResult[RollingStddevReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RollingStddevParams", "RollingStddevRequest", "RollingStddevReport", "normalize_input", "run"]
