"""
quant_strategy_tokenizer.indicators.volatility_regime
======================================================
Purpose: classify volatility regime as an atomic percentile token.
Core idea: Rank historical volatility inside a rolling regime window. Assumes percentile context is more portable across assets than fixed volatility cutoffs.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolatilityRegimeParams, and ModuleRunContext.
Outputs: VolatilityRegimeReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'volatility_regime'
INPUT_KIND = 'price'


@dataclass
class VolatilityRegimeParams(VolatilityParams):
    """Configuration for the volatility_regime volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    regime_window: int = 100


@dataclass
class VolatilityRegimeRequest:
    data: Any
    params: VolatilityRegimeParams = field(default_factory=VolatilityRegimeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolatilityRegimeReport = VolatilityReport


def normalize_input(request: VolatilityRegimeRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: VolatilityRegimeRequest) -> ModuleResult[VolatilityRegimeReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolatilityRegimeParams", "VolatilityRegimeRequest", "VolatilityRegimeReport", "normalize_input", "run"]
