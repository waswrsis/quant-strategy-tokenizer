"""
quant_strategy_tokenizer.indicators.put_call_open_interest_ratio
==================================================================
Purpose: measure put open interest relative to call open interest as an atomic derivatives token.
Core idea: Divide aggregate put OI by call OI. Assumes outstanding option positioning can proxy persistent directional hedging demand.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, PutCallOpenInterestRatioParams, and
ModuleRunContext.
Outputs: PutCallOpenInterestRatioReport with quality, last values, derivative direction, risk
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


INDICATOR = "put_call_open_interest_ratio"


@dataclass
class PutCallOpenInterestRatioParams(DerivativesParams):
    """Configuration for the put_call_open_interest_ratio derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class PutCallOpenInterestRatioRequest:
    data: Any
    params: PutCallOpenInterestRatioParams = field(default_factory=PutCallOpenInterestRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PutCallOpenInterestRatioReport = DerivativesReport


def normalize_input(request: PutCallOpenInterestRatioRequest):
    return normalize_derivatives_input(request)


def run(request: PutCallOpenInterestRatioRequest) -> ModuleResult[PutCallOpenInterestRatioReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["PutCallOpenInterestRatioParams", "PutCallOpenInterestRatioRequest", "PutCallOpenInterestRatioReport", "normalize_input", "run"]
