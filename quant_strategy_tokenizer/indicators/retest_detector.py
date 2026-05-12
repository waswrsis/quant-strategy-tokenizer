"""
quant_strategy_tokenizer.indicators.retest_detector
====================================================
Purpose: detect retests after recent rolling-range breaks as an atomic structure token.
Core idea: Look for price returning near the broken rolling range boundary within retest_bars. Assumes breaks often revisit their origin before continuation.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RetestDetectorParams, and ModuleRunContext.
Outputs: RetestDetectorReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'retest_detector'
INPUT_KIND = 'ohlc'


@dataclass
class RetestDetectorParams(StructureParams):
    """Configuration for the retest_detector structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    retest_bars: int = 10


@dataclass
class RetestDetectorRequest:
    data: Any
    params: RetestDetectorParams = field(default_factory=RetestDetectorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RetestDetectorReport = StructureReport


def normalize_input(request: RetestDetectorRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: RetestDetectorRequest) -> ModuleResult[RetestDetectorReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RetestDetectorParams", "RetestDetectorRequest", "RetestDetectorReport", "normalize_input", "run"]
