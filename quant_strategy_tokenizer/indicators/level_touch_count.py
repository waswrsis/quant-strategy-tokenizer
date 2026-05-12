"""
quant_strategy_tokenizer.indicators.level_touch_count
======================================================
Purpose: count touches across clustered levels as an atomic structure token.
Core idea: Sum touch counts of clustered swing levels. Assumes level strength rises when price revisits a zone repeatedly.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, LevelTouchCountParams, and ModuleRunContext.
Outputs: LevelTouchCountReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'level_touch_count'
INPUT_KIND = 'ohlc'


@dataclass
class LevelTouchCountParams(StructureParams):
    """Configuration for the level_touch_count structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    min_touches: int = 2


@dataclass
class LevelTouchCountRequest:
    data: Any
    params: LevelTouchCountParams = field(default_factory=LevelTouchCountParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


LevelTouchCountReport = StructureReport


def normalize_input(request: LevelTouchCountRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: LevelTouchCountRequest) -> ModuleResult[LevelTouchCountReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["LevelTouchCountParams", "LevelTouchCountRequest", "LevelTouchCountReport", "normalize_input", "run"]
