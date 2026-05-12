"""
quant_strategy_tokenizer.indicators.smma
========================================
Purpose: Smoothed moving average trend token.
Core idea: Compute a Wilder-style recursive moving average. The implementation assumes trends should be smoothed more heavily than a normal EMA, accepting extra lag in exchange for lower noise. Price relative to the smoothed line drives direction.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, SMMAParams, and ModuleRunContext.
Outputs: SMMAReport with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'smma'
INPUT_KIND = 'price'


@dataclass
class SMMAParams(TrendParams):
    """Configuration for the smma trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class SMMARequest:
    data: Any
    params: SMMAParams = field(default_factory=SMMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SMMAReport = TrendReport


def normalize_input(request: SMMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: SMMARequest) -> ModuleResult[SMMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SMMAParams", "SMMARequest", "SMMAReport", "normalize_input", "run"]
