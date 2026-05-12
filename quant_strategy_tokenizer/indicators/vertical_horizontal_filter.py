"""
quant_strategy_tokenizer.indicators.vertical_horizontal_filter
===============================================================
Purpose: calculate Vertical Horizontal Filter as an atomic regime token.
Core idea: Divide net price displacement by summed absolute movement. Assumes efficient directional movement implies lower choppiness and different volatility character.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VerticalHorizontalFilterParams, and ModuleRunContext.
Outputs: VerticalHorizontalFilterReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'vertical_horizontal_filter'
INPUT_KIND = 'price'


@dataclass
class VerticalHorizontalFilterParams(VolatilityParams):
    """Configuration for the vertical_horizontal_filter volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 28


@dataclass
class VerticalHorizontalFilterRequest:
    data: Any
    params: VerticalHorizontalFilterParams = field(default_factory=VerticalHorizontalFilterParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VerticalHorizontalFilterReport = VolatilityReport


def normalize_input(request: VerticalHorizontalFilterRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: VerticalHorizontalFilterRequest) -> ModuleResult[VerticalHorizontalFilterReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VerticalHorizontalFilterParams", "VerticalHorizontalFilterRequest", "VerticalHorizontalFilterReport", "normalize_input", "run"]
