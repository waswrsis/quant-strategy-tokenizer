"""
quant_strategy_tokenizer.indicators.stablecoin_supply_ratio
=============================================================
Purpose: compare stablecoin supply with market value as an atomic on-chain token.
Core idea: Divide stablecoin supply by market cap. Assumes stablecoin liquidity relative to network value can proxy dry powder.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, StablecoinSupplyRatioParams, and
ModuleRunContext.
Outputs: StablecoinSupplyRatioReport with quality, last values, network activity, flow,
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


INDICATOR = "stablecoin_supply_ratio"


@dataclass
class StablecoinSupplyRatioParams(OnChainParams):
    """Configuration for the stablecoin_supply_ratio on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class StablecoinSupplyRatioRequest:
    data: Any
    params: StablecoinSupplyRatioParams = field(default_factory=StablecoinSupplyRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


StablecoinSupplyRatioReport = OnChainReport


def normalize_input(request: StablecoinSupplyRatioRequest):
    return normalize_onchain_input(request)


def run(request: StablecoinSupplyRatioRequest) -> ModuleResult[StablecoinSupplyRatioReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["StablecoinSupplyRatioParams", "StablecoinSupplyRatioRequest", "StablecoinSupplyRatioReport", "normalize_input", "run"]
