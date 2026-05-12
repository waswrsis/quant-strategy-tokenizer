"""
quant_strategy_tokenizer.indicators.volume_advance_decline_percent
===================================================================
Purpose: measure net up/down volume as a percentage of total directional volume as an atomic breadth token.
Core idea: Scale up-volume minus down-volume by total up plus down volume. Assumes normalized volume participation is comparable across samples.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
VolumeAdvanceDeclinePercentParams, and ModuleRunContext.
Outputs: VolumeAdvanceDeclinePercentReport with quality, last values, breadth direction/state,
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


INDICATOR = 'volume_advance_decline_percent'


@dataclass
class VolumeAdvanceDeclinePercentParams(BreadthParams):
    """Configuration for the volume_advance_decline_percent breadth token.

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
class VolumeAdvanceDeclinePercentRequest:
    data: Any
    params: VolumeAdvanceDeclinePercentParams = field(default_factory=VolumeAdvanceDeclinePercentParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


VolumeAdvanceDeclinePercentReport = BreadthReport


def normalize_input(request: VolumeAdvanceDeclinePercentRequest):
    return normalize_breadth_input(request)


def run(request: VolumeAdvanceDeclinePercentRequest) -> ModuleResult[VolumeAdvanceDeclinePercentReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["VolumeAdvanceDeclinePercentParams", "VolumeAdvanceDeclinePercentRequest", "VolumeAdvanceDeclinePercentReport", "normalize_input", "run"]
