"""
quant_strategy_tokenizer.indicators.breadth_thrust
===================================================
Purpose: detect strong upside participation thrust from advance share as an atomic breadth token.
Core idea: Smooth the advance share over a rolling window and compare it with a thrust threshold. Assumes rapid broad participation can mark risk-on regime shifts.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
BreadthThrustParams, and ModuleRunContext.
Outputs: BreadthThrustReport with quality, last values, breadth direction/state,
participation counts, volume breadth fields, signal, regime, optional series,
input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient sample,
insufficient coverage, insufficient history, missing required volume/weight, or
calculation errors return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, index provider, constituent source, broker, or live exchange
access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .breadth_common import BreadthParams, BreadthReport, normalize_breadth_input, run_breadth_indicator


INDICATOR = 'breadth_thrust'


@dataclass
class BreadthThrustParams(BreadthParams):
    """Configuration for the breadth_thrust breadth token.

    Configuration:
    - field names map caller data into timestamp, symbol, close, volume, weight,
      and optional benchmark/index columns.
    - window fields are measured in rows on the breadth time axis.
    - sample and coverage fields decide whether cross-sectional evidence is
      trustworthy enough to report.
    - this module does not fetch data, read accounts, or execute trades.
    """

    window: int = 10
    breadth_thrust_threshold: float = 0.615


@dataclass
class BreadthThrustRequest:
    data: Any
    params: BreadthThrustParams = field(default_factory=BreadthThrustParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BreadthThrustReport = BreadthReport


def normalize_input(request: BreadthThrustRequest):
    return normalize_breadth_input(request)


def run(request: BreadthThrustRequest) -> ModuleResult[BreadthThrustReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["BreadthThrustParams", "BreadthThrustRequest", "BreadthThrustReport", "normalize_input", "run"]
