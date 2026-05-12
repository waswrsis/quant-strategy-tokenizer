"""
quant_strategy_tokenizer.indicators.breadth_freeze_pressure
============================================================
Purpose: diagnose one-sided breadth pressure for risk regime research as an atomic breadth token.
Core idea: Report the larger of advance share and decline share without triggering risk actions. Assumes highly one-sided participation can feed external freeze or observe logic.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
BreadthFreezePressureParams, and ModuleRunContext.
Outputs: BreadthFreezePressureReport with quality, last values, breadth direction/state,
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


INDICATOR = 'breadth_freeze_pressure'


@dataclass
class BreadthFreezePressureParams(BreadthParams):
    """Configuration for the breadth_freeze_pressure breadth token.

    Configuration:
    - field names map caller data into timestamp, symbol, close, volume, weight,
      and optional benchmark/index columns.
    - window fields are measured in rows on the breadth time axis.
    - sample and coverage fields decide whether cross-sectional evidence is
      trustworthy enough to report.
    - this module does not fetch data, read accounts, or execute trades.
    """
    pass


@dataclass
class BreadthFreezePressureRequest:
    data: Any
    params: BreadthFreezePressureParams = field(default_factory=BreadthFreezePressureParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


BreadthFreezePressureReport = BreadthReport


def normalize_input(request: BreadthFreezePressureRequest):
    return normalize_breadth_input(request)


def run(request: BreadthFreezePressureRequest) -> ModuleResult[BreadthFreezePressureReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["BreadthFreezePressureParams", "BreadthFreezePressureRequest", "BreadthFreezePressureReport", "normalize_input", "run"]
