"""
quant_strategy_tokenizer.indicators.qstick
==========================================
Purpose: QStick candle-body momentum token.
Core idea: Average close-open candle bodies over a rolling window. The implementation assumes persistent positive or negative bodies reveal directional pressure independent of wicks.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, QStickParams, and ModuleRunContext.
Outputs: QStickReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'qstick'
INPUT_KIND = 'ohlc_open'


@dataclass
class QStickParams(MomentumParams):
    """Configuration for the qstick momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class QStickRequest:
    data: Any
    params: QStickParams = field(default_factory=QStickParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


QStickReport = MomentumReport


def normalize_input(request: QStickRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: QStickRequest) -> ModuleResult[QStickReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["QStickParams", "QStickRequest", "QStickReport", "normalize_input", "run"]
