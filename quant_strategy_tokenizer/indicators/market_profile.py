"""
quant_strategy_tokenizer.indicators.market_profile
===================================================
Purpose: approximate market profile from OHLCV as an atomic structure token.
Core idea: Use the same close-price bins as a lightweight profile approximation. Assumes this is not a true TPO profile without session/tick data.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, MarketProfileParams, and ModuleRunContext.
Outputs: MarketProfileReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'market_profile'
INPUT_KIND = 'ohlcv'


@dataclass
class MarketProfileParams(StructureParams):
    """Configuration for the market_profile structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    lookback: int = 120
    profile_bins: int = 24


@dataclass
class MarketProfileRequest:
    data: Any
    params: MarketProfileParams = field(default_factory=MarketProfileParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MarketProfileReport = StructureReport


def normalize_input(request: MarketProfileRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: MarketProfileRequest) -> ModuleResult[MarketProfileReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MarketProfileParams", "MarketProfileRequest", "MarketProfileReport", "normalize_input", "run"]
