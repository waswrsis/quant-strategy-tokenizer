"""
quant_strategy_tokenizer.indicators.zscore
===========================================
Purpose: calculate rolling price z-score as an atomic volatility-normalized token.
Core idea: Standardize close against rolling mean and standard deviation. Assumes deviations are interpretable relative to recent dispersion.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ZScoreParams, and ModuleRunContext.
Outputs: ZScoreReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'zscore'
INPUT_KIND = 'price'


@dataclass
class ZScoreParams(VolatilityParams):
    """Configuration for the zscore volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class ZScoreRequest:
    data: Any
    params: ZScoreParams = field(default_factory=ZScoreParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ZScoreReport = VolatilityReport


def normalize_input(request: ZScoreRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: ZScoreRequest) -> ModuleResult[ZScoreReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ZScoreParams", "ZScoreRequest", "ZScoreReport", "normalize_input", "run"]
