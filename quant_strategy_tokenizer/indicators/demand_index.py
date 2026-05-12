"""
quant_strategy_tokenizer.indicators.demand_index
=================================================
Purpose: calculate a demand-index proxy as an atomic pressure token.
Core idea: Normalize rolling price-change times volume by absolute price-volume pressure. Assumes demand pressure can be approximated without bid/ask data.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, DemandIndexParams, and ModuleRunContext.
Outputs: DemandIndexReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'demand_index'
INPUT_KIND = 'price_volume'


@dataclass
class DemandIndexParams(VolumeParams):
    """Configuration for the demand_index volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class DemandIndexRequest:
    data: Any
    params: DemandIndexParams = field(default_factory=DemandIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DemandIndexReport = VolumeReport


def normalize_input(request: DemandIndexRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: DemandIndexRequest) -> ModuleResult[DemandIndexReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DemandIndexParams", "DemandIndexRequest", "DemandIndexReport", "normalize_input", "run"]
