"""
quant_strategy_tokenizer.indicators.zlema
=========================================
Purpose: Zero-lag exponential moving average trend token.
Core idea: Compute EMA on a lag-adjusted price series using price minus its delayed value. The implementation assumes recent momentum can compensate for EMA lag, which may make signals faster but more sensitive to noise.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ZLEMAParams, and ModuleRunContext.
Outputs: ZLEMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'zlema'
INPUT_KIND = 'price'


@dataclass
class ZLEMAParams(TrendParams):
    """Configuration for the zlema trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class ZLEMARequest:
    data: Any
    params: ZLEMAParams = field(default_factory=ZLEMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ZLEMAReport = TrendReport


def normalize_input(request: ZLEMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ZLEMARequest) -> ModuleResult[ZLEMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ZLEMAParams", "ZLEMARequest", "ZLEMAReport", "normalize_input", "run"]
