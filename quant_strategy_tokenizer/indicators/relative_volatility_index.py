"""
quant_strategy_tokenizer.indicators.relative_volatility_index
==============================================================
Purpose: calculate Relative Volatility Index as an atomic volatility-bias token.
Core idea: Apply RSI-style up/down averaging to rolling standard deviation. Assumes volatility associated with up and down closes can reveal directional pressure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RelativeVolatilityIndexParams, and ModuleRunContext.
Outputs: RelativeVolatilityIndexReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'relative_volatility_index'
INPUT_KIND = 'price'


@dataclass
class RelativeVolatilityIndexParams(VolatilityParams):
    """Configuration for the relative_volatility_index volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    fast_window: int = 14
    window: int = 20


@dataclass
class RelativeVolatilityIndexRequest:
    data: Any
    params: RelativeVolatilityIndexParams = field(default_factory=RelativeVolatilityIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RelativeVolatilityIndexReport = VolatilityReport


def normalize_input(request: RelativeVolatilityIndexRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RelativeVolatilityIndexRequest) -> ModuleResult[RelativeVolatilityIndexReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RelativeVolatilityIndexParams", "RelativeVolatilityIndexRequest", "RelativeVolatilityIndexReport", "normalize_input", "run"]
