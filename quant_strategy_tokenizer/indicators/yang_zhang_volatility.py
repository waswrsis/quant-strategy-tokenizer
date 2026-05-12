"""
quant_strategy_tokenizer.indicators.yang_zhang_volatility
==========================================================
Purpose: calculate Yang-Zhang volatility as an atomic volatility token.
Core idea: Blend overnight, open-close, and Rogers-Satchell components. Assumes separate gap and intraday terms produce a more complete OHLC estimator.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, YangZhangVolatilityParams, and ModuleRunContext.
Outputs: YangZhangVolatilityReport with quality, last values, volatility direction, volatility
level, signal, regime, optional series, input profile, used fields, warnings,
and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
unavailable requested backend, or invalid zero-denominator calculations return
ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .volatility_common import VolatilityParams, VolatilityReport, normalize_volatility_input, run_volatility_indicator


INDICATOR = 'yang_zhang_volatility'
INPUT_KIND = 'ohlc_open'


@dataclass
class YangZhangVolatilityParams(VolatilityParams):
    """Configuration for the yang_zhang_volatility volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class YangZhangVolatilityRequest:
    data: Any
    params: YangZhangVolatilityParams = field(default_factory=YangZhangVolatilityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


YangZhangVolatilityReport = VolatilityReport


def normalize_input(request: YangZhangVolatilityRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: YangZhangVolatilityRequest) -> ModuleResult[YangZhangVolatilityReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["YangZhangVolatilityParams", "YangZhangVolatilityRequest", "YangZhangVolatilityReport", "normalize_input", "run"]
