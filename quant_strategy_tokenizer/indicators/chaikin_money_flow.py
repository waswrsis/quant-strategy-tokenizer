"""
quant_strategy_tokenizer.indicators.chaikin_money_flow
=======================================================
Purpose: calculate Chaikin Money Flow as an atomic flow token.
Core idea: Divide rolling money-flow volume by rolling total volume. Assumes close location inside each bar reveals accumulation/distribution pressure.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ChaikinMoneyFlowParams, and ModuleRunContext.
Outputs: ChaikinMoneyFlowReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'chaikin_money_flow'
INPUT_KIND = 'ohlcv'


@dataclass
class ChaikinMoneyFlowParams(VolumeParams):
    """Configuration for the chaikin_money_flow volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class ChaikinMoneyFlowRequest:
    data: Any
    params: ChaikinMoneyFlowParams = field(default_factory=ChaikinMoneyFlowParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ChaikinMoneyFlowReport = VolumeReport


def normalize_input(request: ChaikinMoneyFlowRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: ChaikinMoneyFlowRequest) -> ModuleResult[ChaikinMoneyFlowReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ChaikinMoneyFlowParams", "ChaikinMoneyFlowRequest", "ChaikinMoneyFlowReport", "normalize_input", "run"]
