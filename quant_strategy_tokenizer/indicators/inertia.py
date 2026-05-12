"""
quant_strategy_tokenizer.indicators.inertia
============================================
Purpose: calculate Inertia from Relative Volatility Index as an atomic volatility-bias token.
Core idea: Smooth RVI with a rolling regression endpoint. Assumes persistence in volatility bias is more useful than a raw one-bar RVI value.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, InertiaParams, and ModuleRunContext.
Outputs: InertiaReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'inertia'
INPUT_KIND = 'price'


@dataclass
class InertiaParams(VolatilityParams):
    """Configuration for the inertia volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    fast_window: int = 14
    window: int = 20


@dataclass
class InertiaRequest:
    data: Any
    params: InertiaParams = field(default_factory=InertiaParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


InertiaReport = VolatilityReport


def normalize_input(request: InertiaRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: InertiaRequest) -> ModuleResult[InertiaReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["InertiaParams", "InertiaRequest", "InertiaReport", "normalize_input", "run"]
