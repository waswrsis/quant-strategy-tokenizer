"""
quant_strategy_tokenizer.indicators.relative_vigor_index
========================================================
Purpose: Relative Vigor Index momentum token.
Core idea: Average close-open relative to high-low and compare with a short signal average. The implementation assumes bullish bars close above open with vigor relative to their range.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, RelativeVigorIndexParams, and ModuleRunContext.
Outputs: RelativeVigorIndexReport with quality, last values, momentum direction, signal,
zone, optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .momentum_common import MomentumParams, MomentumReport, normalize_momentum_input, run_momentum_indicator


INDICATOR = 'relative_vigor_index'
INPUT_KIND = 'ohlc_open'


@dataclass
class RelativeVigorIndexParams(MomentumParams):
    """Configuration for the relative_vigor_index momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 0.2
    oversold: float = -0.2


@dataclass
class RelativeVigorIndexRequest:
    data: Any
    params: RelativeVigorIndexParams = field(default_factory=RelativeVigorIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RelativeVigorIndexReport = MomentumReport


def normalize_input(request: RelativeVigorIndexRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: RelativeVigorIndexRequest) -> ModuleResult[RelativeVigorIndexReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RelativeVigorIndexParams", "RelativeVigorIndexRequest", "RelativeVigorIndexReport", "normalize_input", "run"]
