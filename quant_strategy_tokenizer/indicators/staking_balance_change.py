"""
quant_strategy_tokenizer.indicators.staking_balance_change
============================================================
Purpose: measure staking balance change as an atomic on-chain token.
Core idea: Calculate percentage change in staking balance. Assumes staking balance growth reflects locked-supply participation.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, StakingBalanceChangeParams, and
ModuleRunContext.
Outputs: StakingBalanceChangeReport with quality, last values, network activity, flow,
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


INDICATOR = "staking_balance_change"


@dataclass
class StakingBalanceChangeParams(OnChainParams):
    """Configuration for the staking_balance_change on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class StakingBalanceChangeRequest:
    data: Any
    params: StakingBalanceChangeParams = field(default_factory=StakingBalanceChangeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StakingBalanceChangeReport = OnChainReport


def normalize_input(request: StakingBalanceChangeRequest):
    return normalize_onchain_input(request)


def run(request: StakingBalanceChangeRequest) -> ModuleResult[StakingBalanceChangeReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["StakingBalanceChangeParams", "StakingBalanceChangeRequest", "StakingBalanceChangeReport", "normalize_input", "run"]
