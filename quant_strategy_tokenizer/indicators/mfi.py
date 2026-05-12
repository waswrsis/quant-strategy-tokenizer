"""
quant_strategy_tokenizer.indicators.mfi
=======================================
Purpose: Money Flow Index momentum token.
Core idea: Classify typical-price money flow as positive or negative and convert rolling flow ratio into a 0-100 oscillator. The implementation assumes volume-weighted price movement better captures buying/selling pressure than price alone.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MFIParams, and ModuleRunContext.
Outputs: MFIReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'mfi'
INPUT_KIND = 'ohlcv'


@dataclass
class MFIParams(MomentumParams):
    """Configuration for the mfi momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 14
    overbought: float = 80.0
    oversold: float = 20.0


@dataclass
class MFIRequest:
    data: Any
    params: MFIParams = field(default_factory=MFIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MFIReport = MomentumReport


def normalize_input(request: MFIRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: MFIRequest) -> ModuleResult[MFIReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MFIParams", "MFIRequest", "MFIReport", "normalize_input", "run"]
