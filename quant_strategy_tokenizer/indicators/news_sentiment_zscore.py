"""
quant_strategy_tokenizer.indicators.news_sentiment_zscore
===========================================================
Purpose: standardize news sentiment as an atomic sentiment token.
Core idea: Compute a rolling z-score of news sentiment. Assumes news feed sentiment should be judged against its own recent baseline.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, NewsSentimentZScoreParams, and ModuleRunContext.
Outputs: NewsSentimentZScoreReport with quality, last values, sentiment direction/state,
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


INDICATOR = "news_sentiment_zscore"


@dataclass
class NewsSentimentZScoreParams(SentimentParams):
    """Configuration for the news_sentiment_zscore sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class NewsSentimentZScoreRequest:
    data: Any
    params: NewsSentimentZScoreParams = field(default_factory=NewsSentimentZScoreParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NewsSentimentZScoreReport = SentimentReport


def normalize_input(request: NewsSentimentZScoreRequest):
    return normalize_sentiment_input(request)


def run(request: NewsSentimentZScoreRequest) -> ModuleResult[NewsSentimentZScoreReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["NewsSentimentZScoreParams", "NewsSentimentZScoreRequest", "NewsSentimentZScoreReport", "normalize_input", "run"]
