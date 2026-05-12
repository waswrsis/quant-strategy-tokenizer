"""
quant_strategy_tokenizer.indicators.bollinger_keltner_squeeze
==============================================================
Purpose: calculate Bollinger-to-Keltner width ratio as an atomic volatility token.
Core idea: Compare Bollinger width with Keltner width. Assumes ratios below one indicate compression and ratios above one indicate expansion.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, BollingerKeltnerSqueezeParams, and ModuleRunContext.
Outputs: BollingerKeltnerSqueezeReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'bollinger_keltner_squeeze'
INPUT_KIND = 'ohlc'


@dataclass
class BollingerKeltnerSqueezeParams(VolatilityParams):
    """Configuration for the bollinger_keltner_squeeze volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20
    atr_window: int = 14
    stddev_multiplier: float = 2.0
    multiplier: float = 1.5


@dataclass
class BollingerKeltnerSqueezeRequest:
    data: Any
    params: BollingerKeltnerSqueezeParams = field(default_factory=BollingerKeltnerSqueezeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BollingerKeltnerSqueezeReport = VolatilityReport


def normalize_input(request: BollingerKeltnerSqueezeRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: BollingerKeltnerSqueezeRequest) -> ModuleResult[BollingerKeltnerSqueezeReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["BollingerKeltnerSqueezeParams", "BollingerKeltnerSqueezeRequest", "BollingerKeltnerSqueezeReport", "normalize_input", "run"]
