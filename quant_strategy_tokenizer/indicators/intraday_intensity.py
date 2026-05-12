"""
quant_strategy_tokenizer.indicators.intraday_intensity
=======================================================
Purpose: calculate Intraday Intensity as an atomic flow token.
Core idea: Weight volume by where close falls inside the high-low range. Assumes closes near highs imply accumulation and closes near lows imply distribution.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, IntradayIntensityParams, and ModuleRunContext.
Outputs: IntradayIntensityReport with quality, last values, volume direction, volume level,
flow direction, signal, regime, optional series, input profile, used fields,
warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, all-zero volume,
insufficient history, unavailable requested backend, or invalid zero-denominator
calculations return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .volume_common import VolumeParams, VolumeReport, normalize_volume_input, run_volume_indicator


INDICATOR = 'intraday_intensity'
INPUT_KIND = 'ohlcv'


@dataclass
class IntradayIntensityParams(VolumeParams):
    """Configuration for the intraday_intensity volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 21


@dataclass
class IntradayIntensityRequest:
    data: Any
    params: IntradayIntensityParams = field(default_factory=IntradayIntensityParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


IntradayIntensityReport = VolumeReport


def normalize_input(request: IntradayIntensityRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: IntradayIntensityRequest) -> ModuleResult[IntradayIntensityReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["IntradayIntensityParams", "IntradayIntensityRequest", "IntradayIntensityReport", "normalize_input", "run"]
