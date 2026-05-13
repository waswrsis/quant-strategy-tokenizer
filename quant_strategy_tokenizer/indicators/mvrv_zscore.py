"""
quant_strategy_tokenizer.indicators.mvrv_zscore
=================================================
Purpose: standardize MVRV versus recent history as an atomic on-chain token.
Core idea: Compute a rolling z-score of MVRV. Assumes local extremes in cost-basis valuation are more useful than raw levels alone.
Inputs: caller-supplied on-chain rows, age-bucket rows, account/token rows,
DataFrameSpec field mapping, optional ExtractorSpec, MVRVZScoreParams, and
ModuleRunContext.
Outputs: MVRVZScoreReport with quality, last values, network activity, flow,
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


INDICATOR = "mvrv_zscore"


@dataclass
class MVRVZScoreParams(OnChainParams):
    """Configuration for the mvrv_zscore on-chain token.

    Configuration:
    - field-name settings map caller data into network, flow, valuation,
      holder, liquidity, miner/validator, fee, gas, and optional cohort fields.
    - window settings control rolling z-scores, growth rates, and regime
      diagnostics where applicable.
    - threshold settings control qualitative labels only; this module does not
      fetch data, read wallets, read accounts, or place trades.
    """


@dataclass
class MVRVZScoreRequest:
    data: Any
    params: MVRVZScoreParams = field(default_factory=MVRVZScoreParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MVRVZScoreReport = OnChainReport


def normalize_input(request: MVRVZScoreRequest):
    return normalize_onchain_input(request)


def run(request: MVRVZScoreRequest) -> ModuleResult[MVRVZScoreReport]:
    return run_onchain_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["MVRVZScoreParams", "MVRVZScoreRequest", "MVRVZScoreReport", "normalize_input", "run"]
