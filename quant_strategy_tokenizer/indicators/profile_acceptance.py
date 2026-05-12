"""
quant_strategy_tokenizer.indicators.profile_acceptance
=======================================================
Purpose: judge current price acceptance inside approximate value area as an atomic token.
Core idea: Check whether latest close sits inside the OHLCV-derived value area. Assumes acceptance is approximate because true auction data is unavailable.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ProfileAcceptanceParams, and ModuleRunContext.
Outputs: ProfileAcceptanceReport with quality, last values, structure bias/state, nearest
support/resistance, levels, zones, signal, regime, optional series, input
profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
flat price when structure cannot be inferred, invalid profile bins, or invalid
zero-denominator calculations return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, order book, or live exchange
access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .structure_common import StructureParams, StructureReport, normalize_structure_input, run_structure_indicator


INDICATOR = 'profile_acceptance'
INPUT_KIND = 'ohlcv'


@dataclass
class ProfileAcceptanceParams(StructureParams):
    """Configuration for the profile_acceptance structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    lookback: int = 120
    profile_bins: int = 24
    value_area_pct: float = 70.0


@dataclass
class ProfileAcceptanceRequest:
    data: Any
    params: ProfileAcceptanceParams = field(default_factory=ProfileAcceptanceParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ProfileAcceptanceReport = StructureReport


def normalize_input(request: ProfileAcceptanceRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: ProfileAcceptanceRequest) -> ModuleResult[ProfileAcceptanceReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ProfileAcceptanceParams", "ProfileAcceptanceRequest", "ProfileAcceptanceReport", "normalize_input", "run"]
