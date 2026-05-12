"""
quant_strategy_tokenizer.indicators.liquidity_sweep
====================================================
Purpose: detect sweep of prior high or low as an atomic structure token.
Core idea: Flag wicks beyond rolling extremes that close back inside. Assumes wick rejection around prior extremes can proxy liquidity sweeps.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, LiquiditySweepParams, and ModuleRunContext.
Outputs: LiquiditySweepReport with quality, last values, structure bias/state, nearest
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


INDICATOR = 'liquidity_sweep'
INPUT_KIND = 'ohlc'


@dataclass
class LiquiditySweepParams(StructureParams):
    """Configuration for the liquidity_sweep structure token.

    Configuration:
    - field names are logical names resolved by DataFrameSpec.
    - thresholds are fractional unless named as percentages.
    - window and level fields shape report semantics only; this module does not
      place trades or fetch data.
    """

    window: int = 20
    tolerance_pct: float = 0.003


@dataclass
class LiquiditySweepRequest:
    data: Any
    params: LiquiditySweepParams = field(default_factory=LiquiditySweepParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


LiquiditySweepReport = StructureReport


def normalize_input(request: LiquiditySweepRequest):
    return normalize_structure_input(request, INPUT_KIND)


def run(request: LiquiditySweepRequest) -> ModuleResult[LiquiditySweepReport]:
    return run_structure_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["LiquiditySweepParams", "LiquiditySweepRequest", "LiquiditySweepReport", "normalize_input", "run"]
