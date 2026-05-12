"""
quant_strategy_tokenizer.indicators.keltner_channel
====================================================
Module purpose: Keltner channel trend envelope token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, KeltnerChannelParams, and ModuleRunContext.
Outputs: KeltnerChannelReport with quality, last values, trend direction, signal,
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


INDICATOR = 'keltner_channel'
INPUT_KIND = 'ohlc'


@dataclass
class KeltnerChannelParams(TrendParams):
    """Configuration for the keltner_channel trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20
    atr_window: int = 10
    multiplier: float = 2.0


@dataclass
class KeltnerChannelRequest:
    data: Any
    params: KeltnerChannelParams = field(default_factory=KeltnerChannelParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


KeltnerChannelReport = TrendReport


def normalize_input(request: KeltnerChannelRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: KeltnerChannelRequest) -> ModuleResult[KeltnerChannelReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["KeltnerChannelParams", "KeltnerChannelRequest", "KeltnerChannelReport", "normalize_input", "run"]
