"""
quant_strategy_tokenizer.indicators.rocr100
===========================================
Purpose: Rate of Change Ratio 100 momentum token.
Core idea: Calculate the rate-of-change ratio multiplied by 100. The implementation assumes a neutral value of 100, matching TA-Lib-style ratio output.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ROCR100Params, and ModuleRunContext.
Outputs: ROCR100Report with quality, last values, momentum direction, signal,
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


INDICATOR = 'rocr100'
INPUT_KIND = 'price'


@dataclass
class ROCR100Params(MomentumParams):
    """Configuration for the rocr100 momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 100.0
    oversold: float = 100.0


@dataclass
class ROCR100Request:
    data: Any
    params: ROCR100Params = field(default_factory=ROCR100Params)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ROCR100Report = MomentumReport


def normalize_input(request: ROCR100Request):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: ROCR100Request) -> ModuleResult[ROCR100Report]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ROCR100Params", "ROCR100Request", "ROCR100Report", "normalize_input", "run"]
