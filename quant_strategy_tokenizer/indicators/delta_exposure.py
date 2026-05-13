"""
quant_strategy_tokenizer.indicators.delta_exposure
====================================================
Purpose: proxy aggregate delta exposure from supplied Greeks as an atomic derivatives token.
Core idea: Sum delta times open interest and underlying value proxies. Assumes supplied delta and OI represent the chosen chain universe.
Inputs: caller-supplied futures/perpetual rows, option-chain rows, aggregate
rows, DataFrameSpec field mapping, optional ExtractorSpec, DeltaExposureParams, and
ModuleRunContext.
Outputs: DeltaExposureReport with quality, last values, derivative direction, risk
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


INDICATOR = "delta_exposure"


@dataclass
class DeltaExposureParams(DerivativesParams):
    """Configuration for the delta_exposure derivatives token.

    Configuration:
    - field-name settings map caller data into futures/perp/option semantics.
    - window settings control rolling z-scores, momentum, rank, and regime
      diagnostics where applicable.
    - threshold settings control qualitative pressure labels only; this module
      does not fetch data, read accounts, or place trades.
    """


@dataclass
class DeltaExposureRequest:
    data: Any
    params: DeltaExposureParams = field(default_factory=DeltaExposureParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DeltaExposureReport = DerivativesReport


def normalize_input(request: DeltaExposureRequest):
    return normalize_derivatives_input(request)


def run(request: DeltaExposureRequest) -> ModuleResult[DeltaExposureReport]:
    return run_derivatives_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["DeltaExposureParams", "DeltaExposureRequest", "DeltaExposureReport", "normalize_input", "run"]
