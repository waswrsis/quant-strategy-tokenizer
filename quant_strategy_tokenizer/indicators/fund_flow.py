"""
quant_strategy_tokenizer.indicators.fund_flow
===============================================
Purpose: report fund flow sentiment as an atomic sentiment token.
Core idea: Use supplied fund flow directly. Assumes flows are already aligned to the asset or universe being analyzed.
Inputs: caller-supplied survey, social, news, search, flow, positioning,
analyst, insider, policy, or risk-appetite rows, DataFrameSpec field mapping,
optional ExtractorSpec, FundFlowParams, and ModuleRunContext.
Outputs: FundFlowReport with quality, last values, sentiment direction/state,
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


INDICATOR = "fund_flow"


@dataclass
class FundFlowParams(SentimentParams):
    """Configuration for the fund_flow sentiment token.

    Configuration:
    - field-name settings map caller data into survey, social, news, search,
      flow, crowding, analyst, insider, policy, and risk-appetite semantics.
    - window settings control rolling z-scores, momentum, and regime diagnostics
      where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch sentiment feeds, read accounts, or place trades.
    """


@dataclass
class FundFlowRequest:
    data: Any
    params: FundFlowParams = field(default_factory=FundFlowParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FundFlowReport = SentimentReport


def normalize_input(request: FundFlowRequest):
    return normalize_sentiment_input(request)


def run(request: FundFlowRequest) -> ModuleResult[FundFlowReport]:
    return run_sentiment_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["FundFlowParams", "FundFlowRequest", "FundFlowReport", "normalize_input", "run"]
