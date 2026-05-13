"""
quant_strategy_tokenizer.indicators.exchange_reserve_ratio
============================================================
Purpose: measure exchange balance relative to supply as an atomic on-chain token.
Core idea: Divide exchange balance by supply. Assumes a larger exchange reserve share implies more liquid venue-held supply.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, ExchangeReserveRatioParams, and
ModuleRunContext.
Outputs: ExchangeReserveRatioReport with quality, last values, network activity, flow,
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


INDICATOR = "exchange_reserve_ratio"


@dataclass
class ExchangeReserveRatioParams(OnChainParams):
    """Configuration for the exchange_reserve_ratio on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class ExchangeReserveRatioRequest:
    data: Any
    params: ExchangeReserveRatioParams = field(default_factory=ExchangeReserveRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ExchangeReserveRatioReport = OnChainReport


def normalize_input(request: ExchangeReserveRatioRequest):
    return normalize_onchain_input(request)


def run(request: ExchangeReserveRatioRequest) -> ModuleResult[ExchangeReserveRatioReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["ExchangeReserveRatioParams", "ExchangeReserveRatioRequest", "ExchangeReserveRatioReport", "normalize_input", "run"]
