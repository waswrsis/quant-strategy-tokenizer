"""
quant_strategy_tokenizer.indicators.insider_buy_sell_ratio
============================================================
Purpose: measure insider buy to sell value as an atomic sentiment token.
Core idea: Divide insider buy value by sell value. Assumes reported insider transaction values are comparable and relevant to sentiment.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, InsiderBuySellRatioParams, and ModuleRunContext.
Outputs: InsiderBuySellRatioReport with quality, last values, sentiment direction/state,
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


INDICATOR = "insider_buy_sell_ratio"


@dataclass
class InsiderBuySellRatioParams(SentimentParams):
    """Configuration for the insider_buy_sell_ratio sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class InsiderBuySellRatioRequest:
    data: Any
    params: InsiderBuySellRatioParams = field(default_factory=InsiderBuySellRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


InsiderBuySellRatioReport = SentimentReport


def normalize_input(request: InsiderBuySellRatioRequest):
    return normalize_sentiment_input(request)


def run(request: InsiderBuySellRatioRequest) -> ModuleResult[InsiderBuySellRatioReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["InsiderBuySellRatioParams", "InsiderBuySellRatioRequest", "InsiderBuySellRatioReport", "normalize_input", "run"]
