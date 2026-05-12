"""
quant_strategy_tokenizer.indicators.percent_b
==============================================
Purpose: calculate Bollinger percent-b as an atomic volatility-location token.
Core idea: Locate close inside or outside Bollinger bands. Assumes price location within a volatility envelope helps identify stretched states.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, PercentBParams, and ModuleRunContext.
Outputs: PercentBReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'percent_b'
INPUT_KIND = 'price'


@dataclass
class PercentBParams(VolatilityParams):
    """Configuration for the percent_b volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    stddev_multiplier: float = 2.0


@dataclass
class PercentBRequest:
    data: Any
    params: PercentBParams = field(default_factory=PercentBParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PercentBReport = VolatilityReport


def normalize_input(request: PercentBRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: PercentBRequest) -> ModuleResult[PercentBReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["PercentBParams", "PercentBRequest", "PercentBReport", "normalize_input", "run"]
