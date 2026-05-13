"""
quant_strategy_tokenizer.indicators.onchain_risk_regime
=========================================================
Purpose: combine chain valuation and flow risks as an atomic on-chain token.
Core idea: Blend MVRV, NVT, exchange netflow, miner flow, and SOPR pressures. Assumes a composite is more robust than a single chain metric.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, OnchainRiskRegimeParams, and
ModuleRunContext.
Outputs: OnchainRiskRegimeReport with quality, last values, network activity, flow,
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


INDICATOR = "onchain_risk_regime"


@dataclass
class OnchainRiskRegimeParams(OnChainParams):
    """Configuration for the onchain_risk_regime on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class OnchainRiskRegimeRequest:
    data: Any
    params: OnchainRiskRegimeParams = field(default_factory=OnchainRiskRegimeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


OnchainRiskRegimeReport = OnChainReport


def normalize_input(request: OnchainRiskRegimeRequest):
    return normalize_onchain_input(request)


def run(request: OnchainRiskRegimeRequest) -> ModuleResult[OnchainRiskRegimeReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["OnchainRiskRegimeParams", "OnchainRiskRegimeRequest", "OnchainRiskRegimeReport", "normalize_input", "run"]
