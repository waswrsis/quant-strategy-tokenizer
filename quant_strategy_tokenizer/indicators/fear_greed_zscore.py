"""
quant_strategy_tokenizer.indicators.fear_greed_zscore
=======================================================
Purpose: standardize fear-greed readings as an atomic sentiment token.
Core idea: Compute a rolling z-score of fear-greed. Assumes relative fear/greed matters even when the vendor scale is bounded.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, FearGreedZScoreParams, and ModuleRunContext.
Outputs: FearGreedZScoreReport with quality, last values, sentiment direction/state,
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


INDICATOR = "fear_greed_zscore"


@dataclass
class FearGreedZScoreParams(SentimentParams):
    """Configuration for the fear_greed_zscore sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class FearGreedZScoreRequest:
    data: Any
    params: FearGreedZScoreParams = field(default_factory=FearGreedZScoreParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FearGreedZScoreReport = SentimentReport


def normalize_input(request: FearGreedZScoreRequest):
    return normalize_sentiment_input(request)


def run(request: FearGreedZScoreRequest) -> ModuleResult[FearGreedZScoreReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["FearGreedZScoreParams", "FearGreedZScoreRequest", "FearGreedZScoreReport", "normalize_input", "run"]
