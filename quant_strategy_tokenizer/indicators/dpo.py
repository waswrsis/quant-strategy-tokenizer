"""
quant_strategy_tokenizer.indicators.dpo
=======================================
Purpose: Detrended Price Oscillator token.
Core idea: Subtract a displaced rolling mean from current price using a causal variant. The implementation assumes removing a local trend baseline exposes shorter cycle momentum without using future bars.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, DPOParams, and ModuleRunContext.
Outputs: DPOReport with quality, last values, momentum direction, signal,
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


INDICATOR = 'dpo'
INPUT_KIND = 'price'


@dataclass
class DPOParams(MomentumParams):
    """Configuration for the dpo momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 20
    overbought: float = 0.0
    oversold: float = 0.0


@dataclass
class DPORequest:
    data: Any
    params: DPOParams = field(default_factory=DPOParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DPOReport = MomentumReport


def normalize_input(request: DPORequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: DPORequest) -> ModuleResult[DPOReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DPOParams", "DPORequest", "DPOReport", "normalize_input", "run"]
