"""
quant_strategy_tokenizer.indicators.relative_momentum_index
===========================================================
Purpose: Relative Momentum Index token.
Core idea: Apply RSI-style gain/loss smoothing to multi-period momentum instead of one-period changes. The implementation assumes longer-step momentum can reduce noise while preserving bounded RSI semantics.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, RelativeMomentumIndexParams, and ModuleRunContext.
Outputs: RelativeMomentumIndexReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'relative_momentum_index'
INPUT_KIND = 'price'


@dataclass
class RelativeMomentumIndexParams(MomentumParams):
    """Configuration for the relative_momentum_index momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    momentum_window: int = 5
    overbought: float = 70.0
    oversold: float = 30.0


@dataclass
class RelativeMomentumIndexRequest:
    data: Any
    params: RelativeMomentumIndexParams = field(default_factory=RelativeMomentumIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RelativeMomentumIndexReport = MomentumReport


def normalize_input(request: RelativeMomentumIndexRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: RelativeMomentumIndexRequest) -> ModuleResult[RelativeMomentumIndexReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RelativeMomentumIndexParams", "RelativeMomentumIndexRequest", "RelativeMomentumIndexReport", "normalize_input", "run"]
