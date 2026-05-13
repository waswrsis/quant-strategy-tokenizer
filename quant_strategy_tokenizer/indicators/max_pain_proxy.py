"""
quant_strategy_tokenizer.indicators.max_pain_proxy
====================================================
Purpose: estimate the option-chain max-pain price as an atomic derivatives token.
Core idea: Find the strike minimizing open-interest-weighted intrinsic payout across calls and puts. Assumes OI distribution is a proxy and not a forecast.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, MaxPainProxyParams, and
ModuleRunContext.
Outputs: MaxPainProxyReport with quality, last values, derivative direction, risk
state, crowding state, term-structure state, pressure diagnostics, signal,
regime, optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing required derivatives fields,
insufficient history, impossible option-chain aggregation, empty OI/volume,
zero-denominator calculations, or unsupported input shapes return
ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields for futures,
perpetuals, options, or externally aggregated derivatives diagnostics; it does
not assume asset class, venue, contract multiplier, exchange API, or live
account access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .derivatives_common import DerivativesParams, DerivativesReport, normalize_derivatives_input, run_derivatives_indicator


INDICATOR = "max_pain_proxy"


@dataclass
class MaxPainProxyParams(DerivativesParams):
    """Configuration for the max_pain_proxy derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class MaxPainProxyRequest:
    data: Any
    params: MaxPainProxyParams = field(default_factory=MaxPainProxyParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MaxPainProxyReport = DerivativesReport


def normalize_input(request: MaxPainProxyRequest):
    return normalize_derivatives_input(request)


def run(request: MaxPainProxyRequest) -> ModuleResult[MaxPainProxyReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["MaxPainProxyParams", "MaxPainProxyRequest", "MaxPainProxyReport", "normalize_input", "run"]
