"""
quant_strategy_tokenizer.indicators.basis_zscore
==================================================
Purpose: standardize basis pressure against history as an atomic derivatives token.
Core idea: Compute a rolling z-score of basis rate. Assumes relative basis extremes are more portable across instruments than raw spread values.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, BasisZScoreParams, and
ModuleRunContext.
Outputs: BasisZScoreReport with quality, last values, derivative direction, risk
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


INDICATOR = "basis_zscore"


@dataclass
class BasisZScoreParams(DerivativesParams):
    """Configuration for the basis_zscore derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class BasisZScoreRequest:
    data: Any
    params: BasisZScoreParams = field(default_factory=BasisZScoreParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BasisZScoreReport = DerivativesReport


def normalize_input(request: BasisZScoreRequest):
    return normalize_derivatives_input(request)


def run(request: BasisZScoreRequest) -> ModuleResult[BasisZScoreReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["BasisZScoreParams", "BasisZScoreRequest", "BasisZScoreReport", "normalize_input", "run"]
