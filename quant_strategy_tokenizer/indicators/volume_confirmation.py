"""
quant_strategy_tokenizer.indicators.volume_confirmation
========================================================
Purpose: judge price movement confirmation by volume trend as an atomic diagnostic token.
Core idea: Combine rolling price and volume slopes into confirmed, unconfirmed, or distribution-confirmed states. Assumes price moves with rising volume deserve different treatment from moves on fading volume.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, VolumeConfirmationParams, and ModuleRunContext.
Outputs: VolumeConfirmationReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'volume_confirmation'
INPUT_KIND = 'price_volume'


@dataclass
class VolumeConfirmationParams(VolumeParams):
    """Configuration for the volume_confirmation volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class VolumeConfirmationRequest:
    data: Any
    params: VolumeConfirmationParams = field(default_factory=VolumeConfirmationParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeConfirmationReport = VolumeReport


def normalize_input(request: VolumeConfirmationRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: VolumeConfirmationRequest) -> ModuleResult[VolumeConfirmationReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["VolumeConfirmationParams", "VolumeConfirmationRequest", "VolumeConfirmationReport", "normalize_input", "run"]
