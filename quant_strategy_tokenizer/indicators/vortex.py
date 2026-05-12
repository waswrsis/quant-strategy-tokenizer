"""
quant_strategy_tokenizer.indicators.vortex
===========================================
Module purpose: Vortex trend direction token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, VortexParams, and ModuleRunContext.
Outputs: VortexReport with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'vortex'
INPUT_KIND = 'ohlc'


@dataclass
class VortexParams(TrendParams):
    """Configuration for the vortex trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 14


@dataclass
class VortexRequest:
    data: Any
    params: VortexParams = field(default_factory=VortexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VortexReport = TrendReport


def normalize_input(request: VortexRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: VortexRequest) -> ModuleResult[VortexReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VortexParams", "VortexRequest", "VortexReport", "normalize_input", "run"]
