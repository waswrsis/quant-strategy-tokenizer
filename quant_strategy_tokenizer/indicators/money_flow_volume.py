"""
quant_strategy_tokenizer.indicators.money_flow_volume
======================================================
Purpose: calculate raw money-flow volume as an atomic flow token.
Core idea: Multiply close-location value by volume. Assumes intrabar close location is a proxy for signed money flow.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, MoneyFlowVolumeParams, and ModuleRunContext.
Outputs: MoneyFlowVolumeReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'money_flow_volume'
INPUT_KIND = 'ohlcv'


@dataclass
class MoneyFlowVolumeParams(VolumeParams):
    """Configuration for the money_flow_volume volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class MoneyFlowVolumeRequest:
    data: Any
    params: MoneyFlowVolumeParams = field(default_factory=MoneyFlowVolumeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MoneyFlowVolumeReport = VolumeReport


def normalize_input(request: MoneyFlowVolumeRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: MoneyFlowVolumeRequest) -> ModuleResult[MoneyFlowVolumeReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MoneyFlowVolumeParams", "MoneyFlowVolumeRequest", "MoneyFlowVolumeReport", "normalize_input", "run"]
