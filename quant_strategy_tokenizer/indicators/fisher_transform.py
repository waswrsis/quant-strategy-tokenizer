"""
quant_strategy_tokenizer.indicators.fisher_transform
====================================================
Purpose: Fisher Transform oscillator token.
Core idea: Normalize median price within a rolling range, recursively smooth it, and apply the Fisher log transform. The implementation assumes range-normalized prices can be transformed into sharper turning-point signals.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, FisherTransformParams, and ModuleRunContext.
Outputs: FisherTransformReport with quality, last values, momentum direction, signal,
zone, optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .momentum_common import MomentumParams, MomentumReport, normalize_momentum_input, run_momentum_indicator


INDICATOR = 'fisher_transform'
INPUT_KIND = 'ohlc'


@dataclass
class FisherTransformParams(MomentumParams):
    """Configuration for the fisher_transform momentum token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - threshold fields shape report `zone` semantics and do not place trades.
    """

    window: int = 10
    overbought: float = 1.5
    oversold: float = -1.5


@dataclass
class FisherTransformRequest:
    data: Any
    params: FisherTransformParams = field(default_factory=FisherTransformParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


FisherTransformReport = MomentumReport


def normalize_input(request: FisherTransformRequest):
    return normalize_momentum_input(request, INPUT_KIND)


def run(request: FisherTransformRequest) -> ModuleResult[FisherTransformReport]:
    return run_momentum_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["FisherTransformParams", "FisherTransformRequest", "FisherTransformReport", "normalize_input", "run"]
