"""
quant_strategy_tokenizer.indicators.change_of_character
========================================================
Purpose: detect change-of-character style expansion as an atomic structure token.
Core idea: Use the same swing break evidence as break-of-structure but label it as expansion. Assumes CHoCH is a structural diagnostic, not a venue event.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, ChangeOfCharacterParams, and ModuleRunContext.
Outputs: ChangeOfCharacterReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'change_of_character'
INPUT_KIND = 'ohlc'


@dataclass
class ChangeOfCharacterParams(StructureParams):
    """Configuration for the change_of_character structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    breakout_buffer_pct: float = 0.002


@dataclass
class ChangeOfCharacterRequest:
    data: Any
    params: ChangeOfCharacterParams = field(default_factory=ChangeOfCharacterParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ChangeOfCharacterReport = StructureReport


def normalize_input(request: ChangeOfCharacterRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: ChangeOfCharacterRequest) -> ModuleResult[ChangeOfCharacterReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ChangeOfCharacterParams", "ChangeOfCharacterRequest", "ChangeOfCharacterReport", "normalize_input", "run"]
