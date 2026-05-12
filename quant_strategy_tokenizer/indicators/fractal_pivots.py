"""
quant_strategy_tokenizer.indicators.fractal_pivots
===================================================
Purpose: detect fractal-style pivots as an atomic structure token.
Core idea: Use the same local-neighbor pivot logic as swing points with fractal naming. Assumes a pivot is confirmed only after right_bars future bars exist.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, FractalPivotsParams, and ModuleRunContext.
Outputs: FractalPivotsReport with quality, last values, structure bias/state, nearest
support/resistance, levels, zones, signal, regime, optional series, input
profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
flat price when structure cannot be inferred, invalid profile bins, or invalid
zero-denominator calculations return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, order book, or live exchange
access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .structure_common import StructureParams, StructureReport, normalize_structure_input, run_structure_indicator


INDICATOR = 'fractal_pivots'
INPUT_KIND = 'ohlc'


@dataclass
class FractalPivotsParams(StructureParams):
    """Configuration for the fractal_pivots structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    left_bars: int = 2
    right_bars: int = 2


@dataclass
class FractalPivotsRequest:
    data: Any
    params: FractalPivotsParams = field(default_factory=FractalPivotsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FractalPivotsReport = StructureReport


def normalize_input(request: FractalPivotsRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: FractalPivotsRequest) -> ModuleResult[FractalPivotsReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["FractalPivotsParams", "FractalPivotsRequest", "FractalPivotsReport", "normalize_input", "run"]
