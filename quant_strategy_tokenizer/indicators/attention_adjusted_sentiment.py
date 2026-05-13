"""
quant_strategy_tokenizer.indicators.attention_adjusted_sentiment
==================================================================
Purpose: weight sentiment by attention as an atomic sentiment token.
Core idea: Multiply sentiment by bounded attention pressure. Assumes sentiment is more meaningful when attention is elevated.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, AttentionAdjustedSentimentParams, and ModuleRunContext.
Outputs: AttentionAdjustedSentimentReport with quality, last values, sentiment direction/state,
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


INDICATOR = "attention_adjusted_sentiment"


@dataclass
class AttentionAdjustedSentimentParams(SentimentParams):
    """Configuration for the attention_adjusted_sentiment sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class AttentionAdjustedSentimentRequest:
    data: Any
    params: AttentionAdjustedSentimentParams = field(default_factory=AttentionAdjustedSentimentParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AttentionAdjustedSentimentReport = SentimentReport


def normalize_input(request: AttentionAdjustedSentimentRequest):
    return normalize_sentiment_input(request)


def run(request: AttentionAdjustedSentimentRequest) -> ModuleResult[AttentionAdjustedSentimentReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["AttentionAdjustedSentimentParams", "AttentionAdjustedSentimentRequest", "AttentionAdjustedSentimentReport", "normalize_input", "run"]
