"""
quant_strategy_tokenizer.indicators.cycle_pressure_index
==========================================================
Purpose: combine valuation, activity, profit, and flow cycle pressure as an atomic on-chain token.
Core idea: Blend MVRV, NVT, SOPR, network activity, and exchange netflow. Assumes crypto cycle pressure is multi-dimensional.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, CyclePressureIndexParams, and
ModuleRunContext.
Outputs: CyclePressureIndexReport with quality, last values, network activity, flow,
holder, valuation, liquidity, miner/validator, risk, signal, regime, optional
series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing required on-chain fields,
insufficient history, impossible age/entity aggregation, zero-denominator
calculations, or unsupported input shapes return ModuleResult.fail without
hidden fallback.
Market generalization: works on caller-mapped numeric fields for crypto network,
exchange-flow, holder, stablecoin, miner/validator, fee, or externally
aggregated diagnostics; it does not assume chain, asset, vendor schema, wallet
access, account access, or trade execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .onchain_common import OnChainParams, OnChainReport, normalize_onchain_input, run_onchain_indicator


INDICATOR = "cycle_pressure_index"


@dataclass
class CyclePressureIndexParams(OnChainParams):
    """Configuration for the cycle_pressure_index on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class CyclePressureIndexRequest:
    data: Any
    params: CyclePressureIndexParams = field(default_factory=CyclePressureIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


CyclePressureIndexReport = OnChainReport


def normalize_input(request: CyclePressureIndexRequest):
    return normalize_onchain_input(request)


def run(request: CyclePressureIndexRequest) -> ModuleResult[CyclePressureIndexReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["CyclePressureIndexParams", "CyclePressureIndexRequest", "CyclePressureIndexReport", "normalize_input", "run"]
