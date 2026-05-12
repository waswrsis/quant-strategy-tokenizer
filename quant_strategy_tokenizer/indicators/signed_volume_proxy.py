"""
quant_strategy_tokenizer.indicators.signed_volume_proxy
========================================================
Purpose: estimate signed volume from OHLCV as an atomic diagnostic token.
Core idea: Assign volume sign from close-open when available, otherwise close-to-close change. Assumes OHLCV can only proxy direction and must not be treated as true bid/ask delta.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, SignedVolumeProxyParams, and ModuleRunContext.
Outputs: SignedVolumeProxyReport with quality, last values, volume direction, volume level,
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


INDICATOR = 'signed_volume_proxy'
INPUT_KIND = 'ohlcv'


@dataclass
class SignedVolumeProxyParams(VolumeParams):
    """Configuration for the signed_volume_proxy volume token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class SignedVolumeProxyRequest:
    data: Any
    params: SignedVolumeProxyParams = field(default_factory=SignedVolumeProxyParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


SignedVolumeProxyReport = VolumeReport


def normalize_input(request: SignedVolumeProxyRequest):
    return normalize_volume_input(request, INPUT_KIND)


def run(request: SignedVolumeProxyRequest) -> ModuleResult[SignedVolumeProxyReport]:
    return run_volume_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["SignedVolumeProxyParams", "SignedVolumeProxyRequest", "SignedVolumeProxyReport", "normalize_input", "run"]
