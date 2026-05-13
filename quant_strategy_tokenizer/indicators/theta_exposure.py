"""
quant_strategy_tokenizer.indicators.theta_exposure
====================================================
Purpose: proxy aggregate theta exposure from supplied Greeks as an atomic derivatives token.
Core idea: Sum theta times open interest. Assumes supplied theta is already scaled consistently by the data vendor.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, ThetaExposureParams, and
ModuleRunContext.
Outputs: ThetaExposureReport with quality, last values, derivative direction, risk
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


INDICATOR = "theta_exposure"


@dataclass
class ThetaExposureParams(DerivativesParams):
    """Configuration for the theta_exposure derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class ThetaExposureRequest:
    data: Any
    params: ThetaExposureParams = field(default_factory=ThetaExposureParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ThetaExposureReport = DerivativesReport


def normalize_input(request: ThetaExposureRequest):
    return normalize_derivatives_input(request)


def run(request: ThetaExposureRequest) -> ModuleResult[ThetaExposureReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["ThetaExposureParams", "ThetaExposureRequest", "ThetaExposureReport", "normalize_input", "run"]
