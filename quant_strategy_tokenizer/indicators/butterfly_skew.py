"""
quant_strategy_tokenizer.indicators.butterfly_skew
====================================================
Purpose: estimate smile wing richness versus ATM as an atomic derivatives token.
Core idea: Compare wing IV with ATM IV across the supplied smile. Assumes strikes around the underlying approximate the volatility smile.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, ButterflySkewParams, and
ModuleRunContext.
Outputs: ButterflySkewReport with quality, last values, derivative direction, risk
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


INDICATOR = "butterfly_skew"


@dataclass
class ButterflySkewParams(DerivativesParams):
    """Configuration for the butterfly_skew derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class ButterflySkewRequest:
    data: Any
    params: ButterflySkewParams = field(default_factory=ButterflySkewParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ButterflySkewReport = DerivativesReport


def normalize_input(request: ButterflySkewRequest):
    return normalize_derivatives_input(request)


def run(request: ButterflySkewRequest) -> ModuleResult[ButterflySkewReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["ButterflySkewParams", "ButterflySkewRequest", "ButterflySkewReport", "normalize_input", "run"]
