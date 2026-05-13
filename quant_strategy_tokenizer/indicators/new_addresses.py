"""
quant_strategy_tokenizer.indicators.new_addresses
===================================================
Purpose: report new address creation as an atomic on-chain token.
Core idea: Use the supplied new-address series directly. Assumes address creation can proxy user growth while acknowledging address reuse and sybil noise.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, NewAddressesParams, and
ModuleRunContext.
Outputs: NewAddressesReport with quality, last values, network activity, flow,
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


INDICATOR = "new_addresses"


@dataclass
class NewAddressesParams(OnChainParams):
    """Configuration for the new_addresses on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class NewAddressesRequest:
    data: Any
    params: NewAddressesParams = field(default_factory=NewAddressesParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NewAddressesReport = OnChainReport


def normalize_input(request: NewAddressesRequest):
    return normalize_onchain_input(request)


def run(request: NewAddressesRequest) -> ModuleResult[NewAddressesReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["NewAddressesParams", "NewAddressesRequest", "NewAddressesReport", "normalize_input", "run"]
