"""
quant_strategy_tokenizer.indicators.margin_long_short_ratio
=============================================================
Purpose: compare margin long and short balances as an atomic sentiment token.
Core idea: Divide margin long balance by margin short balance. Assumes margin data reflects leveraged retail or venue positioning.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, MarginLongShortRatioParams, and ModuleRunContext.
Outputs: MarginLongShortRatioReport with quality, last values, sentiment direction/state,
attention, crowding, fear/greed, flow, contrarian, risk, signal, regime,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing required sentiment fields,
insufficient history, zero-denominator calculations, or unsupported input shapes
return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields for surveys,
social/news/search feeds, fund flows, positioning, analyst/insider data, policy,
or risk-appetite diagnostics; it does not assume asset class, venue, vendor,
account access, external API access, or trade execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .sentiment_common import SentimentParams, SentimentReport, normalize_sentiment_input, run_sentiment_indicator


INDICATOR = "margin_long_short_ratio"


@dataclass
class MarginLongShortRatioParams(SentimentParams):
    """Configuration for the margin_long_short_ratio sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class MarginLongShortRatioRequest:
    data: Any
    params: MarginLongShortRatioParams = field(default_factory=MarginLongShortRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MarginLongShortRatioReport = SentimentReport


def normalize_input(request: MarginLongShortRatioRequest):
    return normalize_sentiment_input(request)


def run(request: MarginLongShortRatioRequest) -> ModuleResult[MarginLongShortRatioReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["MarginLongShortRatioParams", "MarginLongShortRatioRequest", "MarginLongShortRatioReport", "normalize_input", "run"]
