"""
quant_strategy_tokenizer.indicators.ichimoku_cloud
==================================================
Module purpose: Ichimoku cloud structured trend token.
Core idea: Compute Tenkan, Kijun, Senkou spans, cloud midpoint, and Chikou from rolling high/low midpoints. The implementation assumes multi-horizon range midpoints and displaced spans capture support, resistance, and trend regime.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, IchimokuCloudParams, and ModuleRunContext.
Outputs: IchimokuCloudReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ichimoku_cloud'
INPUT_KIND = 'ohlc'


@dataclass
class IchimokuCloudParams(TrendParams):
    """Configuration for the ichimoku_cloud trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    tenkan_window: int = 9
    kijun_window: int = 26
    senkou_b_window: int = 52
    displacement: int = 26


@dataclass
class IchimokuCloudRequest:
    data: Any
    params: IchimokuCloudParams = field(default_factory=IchimokuCloudParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


IchimokuCloudReport = TrendReport


def normalize_input(request: IchimokuCloudRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: IchimokuCloudRequest) -> ModuleResult[IchimokuCloudReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["IchimokuCloudParams", "IchimokuCloudRequest", "IchimokuCloudReport", "normalize_input", "run"]
