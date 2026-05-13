"""
quant_strategy_tokenizer.indicators.onchain_common
==================================================
Purpose: shared implementation layer for atomic on-chain indicator tokens.
Core idea: Normalize caller-supplied crypto network, exchange-flow, holder,
stablecoin, miner/validator, fee, or age-bucket rows, then compute reusable
on-chain regime diagnostics. Assumes on-chain data is supplied by the caller
and that proxy metrics must stay explicit rather than pretending to be vendor
labels or observed entity inventories.
Inputs: raw user data, optional DataFrameSpec/ExtractorSpec, OnChainParams,
indicator name, and ModuleRunContext.
Outputs: OnChainReport wrapped in ModuleResult with latest values, network,
flow, holder, valuation, liquidity, miner/validator, and risk states, optional
series, diagnostics, warnings, and report files when requested.
Failure semantics: invalid params, missing fields, unsupported input shapes,
insufficient history, zero denominators, unusable age/entity aggregation, and
calculation errors return ModuleResult.fail.
Market generalization: calculations operate on caller-mapped numeric fields and
do not assume chain, asset, vendor schema, wallet access, account access, or
trade execution capability.
"""
from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..reporting import write_module_report


@dataclass
class OnChainParams:
    """Generic on-chain indicator options used by atomic wrapper modules.

    Configuration:
    - field names map caller data into network, flow, valuation, holder,
      stablecoin, miner/validator, fee, gas, and optional entity fields.
    - window fields are rows/bars on the input time axis.
    - thresholds label risk, liquidity, valuation, and extreme z-score states.
    - age thresholds define proxy long-term and short-term holder buckets.
    """

    ts_field: str = "ts"
    price_field: str = "price"
    market_cap_field: str = "market_cap"
    realized_cap_field: str = "realized_cap"
    transfer_volume_field: str = "transfer_volume"
    transaction_count_field: str = "transaction_count"
    active_addresses_field: str = "active_addresses"
    new_addresses_field: str = "new_addresses"
    exchange_inflow_field: str = "exchange_inflow"
    exchange_outflow_field: str = "exchange_outflow"
    exchange_balance_field: str = "exchange_balance"
    miner_reserve_field: str = "miner_reserve"
    miner_flow_field: str = "miner_flow"
    staking_deposits_field: str = "staking_deposits"
    staking_withdrawals_field: str = "staking_withdrawals"
    staking_balance_field: str = "staking_balance"
    supply_field: str = "supply"
    circulating_supply_field: str = "circulating_supply"
    stablecoin_supply_field: str = "stablecoin_supply"
    stablecoin_exchange_balance_field: str = "stablecoin_exchange_balance"
    nvt_field: str = "nvt"
    mvrv_field: str = "mvrv"
    sopr_field: str = "sopr"
    realized_price_field: str = "realized_price"
    utxo_age_field: str = "utxo_age"
    holder_age_field: str = "holder_age"
    whale_balance_field: str = "whale_balance"
    retail_balance_field: str = "retail_balance"
    gas_used_field: str = "gas_used"
    gas_price_field: str = "gas_price"
    fees_field: str = "fees"
    burned_fees_field: str = "burned_fees"
    entity_field: str = "entity"
    age_bucket_field: str = "age_bucket"
    chain_field: str = "chain"
    asset_field: str = "asset"
    window: int = 20
    fast_window: int = 7
    slow_window: int = 30
    regime_window: int = 180
    high_percentile: float = 80.0
    low_percentile: float = 20.0
    extreme_zscore: float = 2.0
    risk_threshold: float = 70.0
    liquidity_threshold: float = 70.0
    long_term_age_days: float = 155.0
    short_term_age_days: float = 155.0


@dataclass
class OnChainReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    network_activity_state: str = "unknown"
    flow_state: str = "unknown"
    holder_state: str = "unknown"
    valuation_state: str = "unknown"
    liquidity_state: str = "unknown"
    miner_validator_state: str = "unknown"
    risk_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    series: Optional[List[Optional[float]]] = None
    series_by_name: Optional[Dict[str, List[Optional[float]]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _OnChainData:
    kind: str
    frame: pd.DataFrame
    used_fields: Dict[str, str] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class _ComputeOutput:
    primary: pd.Series
    series: Dict[str, pd.Series]
    network_activity_state: str = "unknown"
    flow_state: str = "unknown"
    holder_state: str = "unknown"
    valuation_state: str = "unknown"
    liquidity_state: str = "unknown"
    miner_validator_state: str = "unknown"
    risk_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


ONCHAIN_INDICATORS = {
    "active_addresses",
    "new_addresses",
    "transaction_count",
    "transaction_volume",
    "transfer_volume_adjusted",
    "network_activity_index",
    "address_growth_rate",
    "transaction_growth_rate",
    "nvt_ratio",
    "nvt_signal",
    "mvrv_ratio",
    "mvrv_zscore",
    "realized_price",
    "market_realized_gradient",
    "supply_in_profit_proxy",
    "realized_cap_change",
    "exchange_netflow",
    "exchange_inflow_zscore",
    "exchange_outflow_zscore",
    "exchange_balance_change",
    "exchange_reserve_ratio",
    "exchange_flow_pressure",
    "stablecoin_exchange_balance_change",
    "sopr",
    "sopr_zscore",
    "holder_age_trend",
    "long_term_holder_supply_proxy",
    "short_term_holder_supply_proxy",
    "hodl_wave_proxy",
    "whale_balance_change",
    "retail_balance_change",
    "whale_retail_divergence",
    "stablecoin_supply_change",
    "stablecoin_supply_ratio",
    "stablecoin_liquidity_index",
    "stablecoin_exchange_pressure",
    "miner_reserve_change",
    "miner_flow_pressure",
    "miner_capitulation_proxy",
    "staking_deposit_withdrawal_ratio",
    "staking_balance_change",
    "validator_exit_pressure",
    "fee_pressure",
    "gas_usage_trend",
    "gas_price_zscore",
    "fee_burn_pressure",
    "onchain_risk_regime",
    "onchain_liquidity_regime",
    "onchain_valuation_regime",
    "onchain_accumulation_distribution",
    "cycle_pressure_index",
}


PROXY_INDICATORS = {
    "supply_in_profit_proxy",
    "long_term_holder_supply_proxy",
    "short_term_holder_supply_proxy",
    "hodl_wave_proxy",
    "miner_capitulation_proxy",
    "validator_exit_pressure",
}


def normalize_onchain_input(request: Any) -> ModuleResult[_OnChainData]:
    params = request.params
    spec = request.spec or DataFrameSpec()
    raw = _raw_to_frame(request.data, request.extractor)
    if not raw.ok:
        return raw
    frame = raw.value
    if frame is None or frame.empty:
        return ModuleResult.fail("empty_input", "on-chain input contains no rows")
    frame = frame.copy()
    cols = {str(c): c for c in frame.columns}
    used: Dict[str, str] = {}
    field_candidates = {
        "ts": [params.ts_field, spec.ts_col],
        "price": [params.price_field, spec.price_col, spec.value_col, spec.close_col],
        "market_cap": [params.market_cap_field],
        "realized_cap": [params.realized_cap_field],
        "transfer_volume": [params.transfer_volume_field, spec.volume_col],
        "transaction_count": [params.transaction_count_field],
        "active_addresses": [params.active_addresses_field],
        "new_addresses": [params.new_addresses_field],
        "exchange_inflow": [params.exchange_inflow_field],
        "exchange_outflow": [params.exchange_outflow_field],
        "exchange_balance": [params.exchange_balance_field],
        "miner_reserve": [params.miner_reserve_field],
        "miner_flow": [params.miner_flow_field],
        "staking_deposits": [params.staking_deposits_field],
        "staking_withdrawals": [params.staking_withdrawals_field],
        "staking_balance": [params.staking_balance_field],
        "supply": [params.supply_field],
        "circulating_supply": [params.circulating_supply_field],
        "stablecoin_supply": [params.stablecoin_supply_field],
        "stablecoin_exchange_balance": [params.stablecoin_exchange_balance_field],
        "nvt": [params.nvt_field],
        "mvrv": [params.mvrv_field],
        "sopr": [params.sopr_field],
        "realized_price": [params.realized_price_field],
        "utxo_age": [params.utxo_age_field],
        "holder_age": [params.holder_age_field],
        "whale_balance": [params.whale_balance_field],
        "retail_balance": [params.retail_balance_field],
        "gas_used": [params.gas_used_field],
        "gas_price": [params.gas_price_field],
        "fees": [params.fees_field],
        "burned_fees": [params.burned_fees_field],
        "entity": [params.entity_field],
        "age_bucket": [params.age_bucket_field],
        "chain": [params.chain_field],
        "asset": [params.asset_field],
    }
    for logical, names in field_candidates.items():
        col = _find_any_col(cols, names)
        if col is not None:
            used[logical] = str(col)

    if "ts" in used:
        converted = pd.to_datetime(frame[used["ts"]], utc=True, errors="coerce")
        if converted.isna().any():
            return ModuleResult.fail("invalid_timestamp", "timestamp field contains invalid values", field=used["ts"])
        frame["__ts"] = converted
    else:
        frame["__ts"] = pd.RangeIndex(len(frame))

    text_fields = {"ts", "entity", "age_bucket", "chain", "asset"}
    for logical, col in used.items():
        if logical in text_fields:
            continue
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    kind = "age_bucket" if ("age_bucket" in used or "utxo_age" in used or "holder_age" in used) else "entity" if "entity" in used else "aggregate"
    frame = frame.sort_values("__ts").reset_index(drop=True)
    profile = {
        "input_type": type(request.data).__name__,
        "rows": int(len(frame)),
        "columns": [str(c) for c in frame.columns if not str(c).startswith("__")],
    }
    return ModuleResult.success(_OnChainData(kind=kind, frame=frame, used_fields=used, input_profile=profile, warnings=list(raw.warnings)))


def run_onchain_indicator(indicator: str, request: Any, *, module_name: str) -> ModuleResult[OnChainReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error
    norm = normalize_onchain_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    data = norm.value
    if data is None:
        return ModuleResult.fail("internal_error", "on-chain normalization returned no data")

    missing = _missing_required_fields(indicator, data)
    if missing:
        return ModuleResult.fail("missing_required_field", f"{indicator} requires fields: {missing}", details={"missing_fields": missing})
    min_rows = _minimum_rows(indicator, params)
    row_count = _time_row_count(data)
    if row_count < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} time rows, got {row_count}")

    try:
        computed = _compute_indicator(indicator, params, data)
    except ValueError as exc:
        message = str(exc)
        if "no usable numeric values" in message:
            return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output", details={"error": message})
        return ModuleResult.fail("calculation_error", f"{indicator} calculation failed", details={"error": message, "error_type": type(exc).__name__})
    except Exception as exc:
        return ModuleResult.fail("calculation_error", f"{indicator} calculation failed", details={"error": str(exc), "error_type": type(exc).__name__})

    primary = computed.primary.replace([np.inf, -np.inf], np.nan)
    last = _last_float(primary)
    if last is None:
        return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output")
    series_map = {name: ser.replace([np.inf, -np.inf], np.nan) for name, ser in computed.series.items()}
    if "value" not in series_map:
        series_map["value"] = primary
    last_values = {name: _last_float(ser) for name, ser in series_map.items()}
    include_series = detail_at_least(request.context.detail_level, DetailLevel.FULL)
    diagnostics = {"module": module_name, "indicator": indicator, **computed.diagnostics}
    if indicator in PROXY_INDICATORS:
        diagnostics["proxy"] = True
        diagnostics["proxy_note"] = f"{indicator} is a caller-data proxy, not a vendor entity label or directly observed wallet classification."
    report = OnChainReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        network_activity_state=computed.network_activity_state,
        flow_state=computed.flow_state,
        holder_state=computed.holder_state,
        valuation_state=computed.valuation_state,
        liquidity_state=computed.liquidity_state,
        miner_validator_state=computed.miner_validator_state,
        risk_state=computed.risk_state,
        signal=computed.signal,
        regime=computed.regime,
        normalized_value=computed.normalized_value,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": row_count, "input_kind": data.kind, **computed.summary},
        input_profile=data.input_profile,
        used_fields=data.used_fields,
        warnings=data.warnings,
        diagnostics=diagnostics,
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "risk_state": report.risk_state, "regime": report.regime})],
        warnings=data.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _compute_indicator(indicator: str, p: OnChainParams, data: _OnChainData) -> _ComputeOutput:
    active = _optional_series(data, "active_addresses")
    new_addr = _optional_series(data, "new_addresses")
    tx_count = _optional_series(data, "transaction_count")
    transfer = _optional_series(data, "transfer_volume")
    price = _optional_series(data, "price")
    market_cap = _optional_series(data, "market_cap")
    realized_cap = _optional_series(data, "realized_cap")
    exchange_in = _optional_series(data, "exchange_inflow")
    exchange_out = _optional_series(data, "exchange_outflow")
    exchange_bal = _optional_series(data, "exchange_balance")
    miner_reserve = _optional_series(data, "miner_reserve")
    miner_flow = _optional_series(data, "miner_flow")
    staking_dep = _optional_series(data, "staking_deposits")
    staking_wd = _optional_series(data, "staking_withdrawals")
    staking_bal = _optional_series(data, "staking_balance")
    stable_supply = _optional_series(data, "stablecoin_supply")
    stable_exchange = _optional_series(data, "stablecoin_exchange_balance")
    sopr = _optional_series(data, "sopr")
    whale = _optional_series(data, "whale_balance")
    retail = _optional_series(data, "retail_balance")
    gas_used = _optional_series(data, "gas_used")
    gas_price = _optional_series(data, "gas_price")
    fees = _optional_series(data, "fees")
    burned = _optional_series(data, "burned_fees")

    nvt = _safe_compute(lambda: _nvt_ratio(data))
    mvrv = _safe_compute(lambda: _mvrv_ratio(data))
    realized_price = _safe_compute(lambda: _realized_price(data))
    exchange_net = _safe_compute(lambda: _exchange_netflow(data))
    supply = _safe_compute(lambda: _supply(data))
    stable_ratio = _safe_compute(lambda: _stablecoin_supply_ratio(data))
    network_index = _safe_compute(lambda: _network_activity_index(active, new_addr, tx_count, transfer, p))

    if indicator == "active_addresses":
        primary = _require_series(active, "active_addresses")
    elif indicator == "new_addresses":
        primary = _require_series(new_addr, "new_addresses")
    elif indicator == "transaction_count":
        primary = _require_series(tx_count, "transaction_count")
    elif indicator == "transaction_volume":
        primary = _require_series(transfer, "transfer_volume")
    elif indicator == "transfer_volume_adjusted":
        primary = _transfer_volume_adjusted(data)
    elif indicator == "network_activity_index":
        primary = _require_series(network_index, "network_activity_index")
    elif indicator == "address_growth_rate":
        primary = _require_series(active, "active_addresses").pct_change(int(p.fast_window), fill_method=None) * 100.0
    elif indicator == "transaction_growth_rate":
        primary = _require_series(tx_count, "transaction_count").pct_change(int(p.fast_window), fill_method=None) * 100.0
    elif indicator == "nvt_ratio":
        primary = _require_series(nvt, "nvt_ratio")
    elif indicator == "nvt_signal":
        primary = _require_series(nvt, "nvt_ratio").rolling(int(p.window), min_periods=int(p.window)).mean()
    elif indicator == "mvrv_ratio":
        primary = _require_series(mvrv, "mvrv_ratio")
    elif indicator == "mvrv_zscore":
        primary = _zscore(_require_series(mvrv, "mvrv_ratio"), int(p.window))
    elif indicator == "realized_price":
        primary = _require_series(realized_price, "realized_price")
    elif indicator == "market_realized_gradient":
        primary = _require_series(market_cap, "market_cap").pct_change(int(p.window), fill_method=None) * 100.0 - _require_series(realized_cap, "realized_cap").pct_change(int(p.window), fill_method=None) * 100.0
    elif indicator == "supply_in_profit_proxy":
        primary = ((_require_series(price, "price") / _require_series(realized_price, "realized_price").replace(0, np.nan)) - 1.0).clip(lower=-1.0, upper=1.0) * 50.0 + 50.0
    elif indicator == "realized_cap_change":
        primary = _require_series(realized_cap, "realized_cap").pct_change(fill_method=None) * 100.0
    elif indicator == "exchange_netflow":
        primary = _require_series(exchange_net, "exchange_netflow")
    elif indicator == "exchange_inflow_zscore":
        primary = _zscore(_require_series(exchange_in, "exchange_inflow"), int(p.window))
    elif indicator == "exchange_outflow_zscore":
        primary = _zscore(_require_series(exchange_out, "exchange_outflow"), int(p.window))
    elif indicator == "exchange_balance_change":
        primary = _require_series(exchange_bal, "exchange_balance").pct_change(fill_method=None) * 100.0
    elif indicator == "exchange_reserve_ratio":
        primary = _require_series(exchange_bal, "exchange_balance") / _require_series(supply, "supply").replace(0, np.nan) * 100.0
    elif indicator == "exchange_flow_pressure":
        primary = _zscore(_require_series(exchange_net, "exchange_netflow"), int(p.window))
    elif indicator == "stablecoin_exchange_balance_change":
        primary = _require_series(stable_exchange, "stablecoin_exchange_balance").pct_change(fill_method=None) * 100.0
    elif indicator == "sopr":
        primary = _require_series(sopr, "sopr")
    elif indicator == "sopr_zscore":
        primary = _zscore(_require_series(sopr, "sopr"), int(p.window))
    elif indicator == "holder_age_trend":
        primary = _holder_age_series(data).diff(int(p.fast_window))
    elif indicator == "long_term_holder_supply_proxy":
        primary = _age_supply(data, p, "long")
    elif indicator == "short_term_holder_supply_proxy":
        primary = _age_supply(data, p, "short")
    elif indicator == "hodl_wave_proxy":
        long_supply = _age_supply(data, p, "long")
        short_supply = _age_supply(data, p, "short")
        primary = long_supply / (long_supply + short_supply).replace(0, np.nan) * 100.0
    elif indicator == "whale_balance_change":
        primary = _require_series(whale, "whale_balance").pct_change(fill_method=None) * 100.0
    elif indicator == "retail_balance_change":
        primary = _require_series(retail, "retail_balance").pct_change(fill_method=None) * 100.0
    elif indicator == "whale_retail_divergence":
        primary = _require_series(whale, "whale_balance").pct_change(int(p.fast_window), fill_method=None) * 100.0 - _require_series(retail, "retail_balance").pct_change(int(p.fast_window), fill_method=None) * 100.0
    elif indicator == "stablecoin_supply_change":
        primary = _require_series(stable_supply, "stablecoin_supply").pct_change(fill_method=None) * 100.0
    elif indicator == "stablecoin_supply_ratio":
        primary = _require_series(stable_ratio, "stablecoin_supply_ratio")
    elif indicator == "stablecoin_liquidity_index":
        primary = _stablecoin_liquidity_index(stable_supply, stable_exchange, p)
    elif indicator == "stablecoin_exchange_pressure":
        primary = _require_series(stable_exchange, "stablecoin_exchange_balance") / _require_series(stable_supply, "stablecoin_supply").replace(0, np.nan) * 100.0
    elif indicator == "miner_reserve_change":
        primary = _require_series(miner_reserve, "miner_reserve").pct_change(fill_method=None) * 100.0
    elif indicator == "miner_flow_pressure":
        primary = _zscore(_require_series(miner_flow, "miner_flow"), int(p.window))
    elif indicator == "miner_capitulation_proxy":
        reserve_change = _require_series(miner_reserve, "miner_reserve").pct_change(int(p.fast_window), fill_method=None) * -100.0
        flow_pressure = _zscore(_require_series(miner_flow, "miner_flow"), int(p.window))
        primary = pd.concat([reserve_change, flow_pressure], axis=1).mean(axis=1)
    elif indicator == "staking_deposit_withdrawal_ratio":
        primary = _require_series(staking_dep, "staking_deposits") / _require_series(staking_wd, "staking_withdrawals").replace(0, np.nan)
    elif indicator == "staking_balance_change":
        primary = _require_series(staking_bal, "staking_balance").pct_change(fill_method=None) * 100.0
    elif indicator == "validator_exit_pressure":
        primary = _require_series(staking_wd, "staking_withdrawals") / _require_series(staking_bal, "staking_balance").replace(0, np.nan) * 100.0
    elif indicator == "fee_pressure":
        primary = _require_series(fees, "fees") / _require_series(transfer, "transfer_volume").replace(0, np.nan) * 100.0
    elif indicator == "gas_usage_trend":
        primary = _require_series(gas_used, "gas_used").pct_change(int(p.fast_window), fill_method=None) * 100.0
    elif indicator == "gas_price_zscore":
        primary = _zscore(_require_series(gas_price, "gas_price"), int(p.window))
    elif indicator == "fee_burn_pressure":
        primary = _require_series(burned, "burned_fees") / _require_series(fees, "fees").replace(0, np.nan) * 100.0
    elif indicator == "onchain_risk_regime":
        primary = _composite_pressure([_safe_zscore(mvrv, p), _safe_zscore(nvt, p), _safe_zscore(exchange_net, p), _safe_zscore(miner_flow, p), _safe_zscore(sopr, p)], p)
    elif indicator == "onchain_liquidity_regime":
        primary = _stablecoin_liquidity_index(stable_supply, stable_exchange, p)
    elif indicator == "onchain_valuation_regime":
        primary = _composite_pressure([_safe_zscore(mvrv, p), _safe_zscore(nvt, p), _safe_zscore(sopr, p)], p)
    elif indicator == "onchain_accumulation_distribution":
        whale_retail = _require_series(whale, "whale_balance").pct_change(int(p.fast_window), fill_method=None) * 100.0 - _require_series(retail, "retail_balance").pct_change(int(p.fast_window), fill_method=None) * 100.0
        primary = whale_retail - _zscore(_require_series(exchange_net, "exchange_netflow"), int(p.window))
    elif indicator == "cycle_pressure_index":
        primary = _composite_pressure([_safe_zscore(mvrv, p), _safe_zscore(nvt, p), _safe_zscore(sopr, p), _safe_zscore(network_index, p), _safe_zscore(exchange_net, p)], p)
    else:
        raise ValueError(f"unsupported on-chain indicator {indicator}")

    network_state = _network_state(_last_float(network_index), p)
    flow_state = _flow_state(_last_float(exchange_net))
    holder_state = _holder_state(_last_float(_optional_whale_retail(whale, retail, p)))
    valuation_state = _valuation_state(_last_float(mvrv), _last_float(nvt), _last_float(primary), indicator, p)
    liquidity_state = _liquidity_state(_last_float(_optional_pct_change(stable_supply)), _last_float(stable_ratio))
    miner_validator_state = _miner_validator_state(_last_float(miner_flow), _last_float(_optional_pct_change(staking_bal)))
    normalized = _normalized(primary, p)
    risk_state = _risk_state(normalized, p)
    series = {"value": primary}
    for name, ser in (
        ("price", price),
        ("active_addresses", active),
        ("new_addresses", new_addr),
        ("transaction_count", tx_count),
        ("transfer_volume", transfer),
        ("nvt_ratio", nvt),
        ("mvrv_ratio", mvrv),
        ("realized_price", realized_price),
        ("exchange_netflow", exchange_net),
        ("stablecoin_supply_ratio", stable_ratio),
        ("network_activity_index", network_index),
        ("sopr", sopr),
        ("miner_flow", miner_flow),
    ):
        if ser is not None:
            series[name] = ser
    return _ComputeOutput(
        primary=primary,
        series=series,
        network_activity_state=network_state,
        flow_state=flow_state,
        holder_state=holder_state,
        valuation_state=valuation_state,
        liquidity_state=liquidity_state,
        miner_validator_state=miner_validator_state,
        risk_state=risk_state,
        signal=_signal_from_states(risk_state, flow_state, valuation_state, liquidity_state),
        regime=risk_state,
        normalized_value=normalized,
        summary={"calculation": indicator},
    )


def _validate_params(p: OnChainParams) -> Optional[ModuleResult[Any]]:
    for name in ("window", "fast_window", "slow_window", "regime_window"):
        try:
            value = int(getattr(p, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if int(p.fast_window) >= int(p.slow_window):
        return ModuleResult.fail("invalid_parameter", "fast_window must be smaller than slow_window", field="fast_window")
    for name in ("high_percentile", "low_percentile", "risk_threshold", "liquidity_threshold"):
        value = _safe_float(getattr(p, name))
        if value is None or value < 0.0 or value > 100.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be between 0 and 100", field=name)
    if float(p.low_percentile) >= float(p.high_percentile):
        return ModuleResult.fail("invalid_parameter", "low_percentile must be below high_percentile", field="low_percentile")
    if _safe_float(p.extreme_zscore) is None or float(p.extreme_zscore) <= 0.0:
        return ModuleResult.fail("invalid_parameter", "extreme_zscore must be positive", field="extreme_zscore")
    for name in ("long_term_age_days", "short_term_age_days"):
        value = _safe_float(getattr(p, name))
        if value is None or value <= 0.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    return None


def _missing_required_fields(indicator: str, data: _OnChainData) -> List[str]:
    used = data.used_fields
    req: Dict[str, List[str]] = {
        "active_addresses": ["active_addresses"],
        "new_addresses": ["new_addresses"],
        "transaction_count": ["transaction_count"],
        "transaction_volume": ["transfer_volume"],
        "transfer_volume_adjusted": ["transfer_volume"],
        "address_growth_rate": ["active_addresses"],
        "transaction_growth_rate": ["transaction_count"],
        "market_realized_gradient": ["market_cap", "realized_cap"],
        "realized_cap_change": ["realized_cap"],
        "exchange_netflow": ["exchange_inflow", "exchange_outflow"],
        "exchange_inflow_zscore": ["exchange_inflow"],
        "exchange_outflow_zscore": ["exchange_outflow"],
        "exchange_balance_change": ["exchange_balance"],
        "exchange_reserve_ratio": ["exchange_balance"],
        "exchange_flow_pressure": ["exchange_inflow", "exchange_outflow"],
        "stablecoin_exchange_balance_change": ["stablecoin_exchange_balance"],
        "sopr": ["sopr"],
        "sopr_zscore": ["sopr"],
        "whale_balance_change": ["whale_balance"],
        "retail_balance_change": ["retail_balance"],
        "whale_retail_divergence": ["whale_balance", "retail_balance"],
        "stablecoin_supply_change": ["stablecoin_supply"],
        "stablecoin_supply_ratio": ["stablecoin_supply", "market_cap"],
        "stablecoin_liquidity_index": ["stablecoin_supply"],
        "stablecoin_exchange_pressure": ["stablecoin_supply", "stablecoin_exchange_balance"],
        "miner_reserve_change": ["miner_reserve"],
        "miner_flow_pressure": ["miner_flow"],
        "miner_capitulation_proxy": ["miner_reserve", "miner_flow"],
        "staking_deposit_withdrawal_ratio": ["staking_deposits", "staking_withdrawals"],
        "staking_balance_change": ["staking_balance"],
        "validator_exit_pressure": ["staking_withdrawals", "staking_balance"],
        "fee_pressure": ["fees", "transfer_volume"],
        "gas_usage_trend": ["gas_used"],
        "gas_price_zscore": ["gas_price"],
        "fee_burn_pressure": ["burned_fees", "fees"],
        "onchain_accumulation_distribution": ["whale_balance", "retail_balance", "exchange_inflow", "exchange_outflow"],
    }
    if indicator in {"nvt_ratio", "nvt_signal"}:
        return [] if "nvt" in used or ("market_cap" in used and "transfer_volume" in used) else ["nvt or market_cap plus transfer_volume"]
    if indicator in {"mvrv_ratio", "mvrv_zscore"}:
        return [] if "mvrv" in used or ("market_cap" in used and "realized_cap" in used) else ["mvrv or market_cap plus realized_cap"]
    if indicator == "realized_price":
        return [] if "realized_price" in used or ("realized_cap" in used and ("supply" in used or "circulating_supply" in used)) else ["realized_price or realized_cap plus supply/circulating_supply"]
    if indicator == "supply_in_profit_proxy":
        missing = []
        if "price" not in used:
            missing.append("price")
        if "realized_price" not in used and not ("realized_cap" in used and ("supply" in used or "circulating_supply" in used)):
            missing.append("realized_price or realized_cap plus supply/circulating_supply")
        return missing
    if indicator in {"network_activity_index", "cycle_pressure_index"}:
        return [] if any(name in used for name in ("active_addresses", "new_addresses", "transaction_count", "transfer_volume")) else ["one of active_addresses/new_addresses/transaction_count/transfer_volume"]
    if indicator in {"long_term_holder_supply_proxy", "short_term_holder_supply_proxy", "hodl_wave_proxy"}:
        missing = []
        if "supply" not in used and "circulating_supply" not in used:
            missing.append("supply or circulating_supply")
        if "utxo_age" not in used and "holder_age" not in used:
            missing.append("utxo_age or holder_age")
        return missing
    if indicator in {"holder_age_trend"}:
        return [] if "utxo_age" in used or "holder_age" in used else ["utxo_age or holder_age"]
    if indicator in {"onchain_risk_regime", "onchain_valuation_regime"}:
        return [] if ("mvrv" in used or ("market_cap" in used and "realized_cap" in used)) and ("nvt" in used or ("market_cap" in used and "transfer_volume" in used)) else ["mvrv/mcap-realized_cap and nvt/mcap-transfer_volume"]
    if indicator == "onchain_liquidity_regime":
        return [] if "stablecoin_supply" in used else ["stablecoin_supply"]
    required = req.get(indicator, [])
    return [name for name in required if name not in used]


def _minimum_rows(indicator: str, p: OnChainParams) -> int:
    if indicator.endswith("_zscore") or indicator in {"nvt_signal", "network_activity_index", "onchain_risk_regime", "onchain_liquidity_regime", "onchain_valuation_regime", "cycle_pressure_index"}:
        return int(p.window)
    if indicator.endswith("_change") or indicator.endswith("_trend") or indicator.endswith("_growth_rate") or indicator in {"market_realized_gradient", "whale_retail_divergence", "onchain_accumulation_distribution"}:
        return max(2, int(p.fast_window))
    return 1


def _time_row_count(data: _OnChainData) -> int:
    return int(data.frame["__ts"].nunique())


def _time_series(data: _OnChainData, logical: str, agg: str = "last") -> Optional[pd.Series]:
    col = data.used_fields.get(logical)
    if col is None:
        return None
    grouped = data.frame.groupby("__ts", sort=True)[col]
    if agg == "sum":
        out = grouped.sum(min_count=1)
    elif agg == "mean":
        out = grouped.mean()
    else:
        out = grouped.last()
    return pd.to_numeric(out, errors="coerce")


def _optional_series(data: _OnChainData, logical: str) -> Optional[pd.Series]:
    agg = "sum" if logical in {"transfer_volume", "transaction_count", "exchange_inflow", "exchange_outflow", "miner_flow", "staking_deposits", "staking_withdrawals", "fees", "burned_fees", "gas_used"} else "last"
    return _time_series(data, logical, agg=agg)


def _require_series(series: Optional[pd.Series], name: str) -> pd.Series:
    if series is None or series.dropna().empty:
        raise ValueError(f"{name} has no usable numeric values")
    return series


def _nvt_ratio(data: _OnChainData) -> pd.Series:
    nvt = _optional_series(data, "nvt")
    if nvt is not None and not nvt.dropna().empty:
        return nvt
    market_cap = _require_series(_optional_series(data, "market_cap"), "market_cap")
    transfer = _require_series(_optional_series(data, "transfer_volume"), "transfer_volume")
    return market_cap / transfer.replace(0, np.nan)


def _mvrv_ratio(data: _OnChainData) -> pd.Series:
    mvrv = _optional_series(data, "mvrv")
    if mvrv is not None and not mvrv.dropna().empty:
        return mvrv
    market_cap = _require_series(_optional_series(data, "market_cap"), "market_cap")
    realized_cap = _require_series(_optional_series(data, "realized_cap"), "realized_cap")
    return market_cap / realized_cap.replace(0, np.nan)


def _realized_price(data: _OnChainData) -> pd.Series:
    rp = _optional_series(data, "realized_price")
    if rp is not None and not rp.dropna().empty:
        return rp
    realized_cap = _require_series(_optional_series(data, "realized_cap"), "realized_cap")
    return realized_cap / _supply(data).replace(0, np.nan)


def _supply(data: _OnChainData) -> pd.Series:
    supply = _optional_series(data, "supply")
    if supply is not None and not supply.dropna().empty:
        return supply
    return _require_series(_optional_series(data, "circulating_supply"), "supply or circulating_supply")


def _exchange_netflow(data: _OnChainData) -> pd.Series:
    return _require_series(_optional_series(data, "exchange_inflow"), "exchange_inflow") - _require_series(_optional_series(data, "exchange_outflow"), "exchange_outflow")


def _transfer_volume_adjusted(data: _OnChainData) -> pd.Series:
    transfer = _require_series(_optional_series(data, "transfer_volume"), "transfer_volume")
    market_cap = _optional_series(data, "market_cap")
    if market_cap is not None and not market_cap.dropna().empty:
        return transfer / market_cap.replace(0, np.nan) * 100.0
    return transfer


def _network_activity_index(active: Optional[pd.Series], new_addr: Optional[pd.Series], tx_count: Optional[pd.Series], transfer: Optional[pd.Series], p: OnChainParams) -> pd.Series:
    parts = []
    for ser in (active, new_addr, tx_count, transfer):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(_bounded_zscore(ser, int(p.window)))
    if not parts:
        raise ValueError("not enough network fields to compute activity index")
    return pd.concat(parts, axis=1).mean(axis=1)


def _stablecoin_supply_ratio(data: _OnChainData) -> pd.Series:
    stable = _require_series(_optional_series(data, "stablecoin_supply"), "stablecoin_supply")
    market_cap = _require_series(_optional_series(data, "market_cap"), "market_cap")
    return stable / market_cap.replace(0, np.nan) * 100.0


def _stablecoin_liquidity_index(stable_supply: Optional[pd.Series], stable_exchange: Optional[pd.Series], p: OnChainParams) -> pd.Series:
    parts = []
    if stable_supply is not None and len(stable_supply.dropna()) >= int(p.window):
        parts.append(_bounded_zscore(stable_supply, int(p.window)))
    if stable_exchange is not None and len(stable_exchange.dropna()) >= int(p.window):
        parts.append(_bounded_zscore(stable_exchange, int(p.window)))
    if not parts:
        raise ValueError("not enough stablecoin fields to compute liquidity index")
    return pd.concat(parts, axis=1).mean(axis=1)


def _holder_age_series(data: _OnChainData) -> pd.Series:
    age = _optional_series(data, "holder_age")
    if age is not None and not age.dropna().empty:
        return age
    return _require_series(_optional_series(data, "utxo_age"), "holder_age or utxo_age")


def _age_supply(data: _OnChainData, p: OnChainParams, side: str) -> pd.Series:
    age_col = data.used_fields.get("holder_age") or data.used_fields.get("utxo_age")
    supply_col = data.used_fields.get("supply") or data.used_fields.get("circulating_supply")
    if age_col is None or supply_col is None:
        raise ValueError("age supply proxy requires age and supply fields")
    frame = data.frame[["__ts", age_col, supply_col]].copy()
    frame[age_col] = pd.to_numeric(frame[age_col], errors="coerce")
    frame[supply_col] = pd.to_numeric(frame[supply_col], errors="coerce")
    if side == "long":
        mask = frame[age_col] >= float(p.long_term_age_days)
    else:
        mask = frame[age_col] < float(p.short_term_age_days)
    out = frame.loc[mask].groupby("__ts", sort=True)[supply_col].sum(min_count=1)
    all_idx = data.frame.groupby("__ts", sort=True).size().index
    return out.reindex(all_idx)


def _optional_pct_change(series: Optional[pd.Series]) -> Optional[pd.Series]:
    if series is None or series.dropna().empty:
        return None
    return series.pct_change(fill_method=None) * 100.0


def _optional_whale_retail(whale: Optional[pd.Series], retail: Optional[pd.Series], p: OnChainParams) -> Optional[pd.Series]:
    if whale is None or retail is None:
        return None
    return whale.pct_change(int(p.fast_window), fill_method=None) * 100.0 - retail.pct_change(int(p.fast_window), fill_method=None) * 100.0


def _safe_compute(fn: Any) -> Optional[pd.Series]:
    try:
        return fn()
    except Exception:
        return None


def _zscore(series: pd.Series, n: int) -> pd.Series:
    mean = series.rolling(n, min_periods=n).mean()
    std = series.rolling(n, min_periods=n).std(ddof=0).replace(0, np.nan)
    return (series - mean) / std


def _safe_zscore(series: Optional[pd.Series], p: OnChainParams) -> Optional[pd.Series]:
    if series is None or len(series.dropna()) < int(p.window):
        return None
    return _zscore(series, int(p.window))


def _bounded_zscore(series: pd.Series, n: int) -> pd.Series:
    return (_zscore(series, n).clip(lower=-5.0, upper=5.0) + 5.0) / 10.0 * 100.0


def _composite_pressure(parts: List[Optional[pd.Series]], p: OnChainParams) -> pd.Series:
    usable = []
    for ser in parts:
        if ser is not None and not ser.dropna().empty:
            usable.append(ser.abs().clip(upper=5.0) / 5.0 * 100.0)
    if not usable:
        raise ValueError("not enough fields to compute on-chain composite")
    return pd.concat(usable, axis=1).mean(axis=1)


def _network_state(value: Optional[float], p: OnChainParams) -> str:
    if value is None:
        return "unknown"
    if value >= float(p.high_percentile):
        return "high_activity"
    if value <= float(p.low_percentile):
        return "low_activity"
    return "normal_activity"


def _flow_state(netflow: Optional[float]) -> str:
    if netflow is None:
        return "unknown"
    if netflow > 0:
        return "exchange_inflow_pressure"
    if netflow < 0:
        return "exchange_outflow_accumulation"
    return "neutral"


def _holder_state(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value > 0:
        return "accumulation"
    if value < 0:
        return "distribution"
    return "neutral"


def _valuation_state(mvrv: Optional[float], nvt: Optional[float], primary: Optional[float], indicator: str, p: OnChainParams) -> str:
    value = mvrv if mvrv is not None else primary
    if value is None:
        return "unknown"
    if indicator in {"nvt_ratio", "nvt_signal"} and nvt is not None:
        value = nvt
    if value >= 3.0:
        return "overvalued"
    if value <= 1.0:
        return "undervalued"
    return "fair"


def _liquidity_state(stable_change: Optional[float], stable_ratio: Optional[float]) -> str:
    value = stable_change if stable_change is not None else stable_ratio
    if value is None:
        return "unknown"
    if value > 0:
        return "expanding"
    if value < 0:
        return "contracting"
    return "stable"


def _miner_validator_state(miner_flow: Optional[float], staking_change: Optional[float]) -> str:
    value = miner_flow if miner_flow is not None else staking_change
    if value is None:
        return "unknown"
    if value > 0:
        return "pressure"
    if value < 0:
        return "accumulation"
    return "stable"


def _risk_state(value: Optional[float], p: OnChainParams) -> str:
    if value is None:
        return "unknown"
    if value >= max(float(p.risk_threshold), float(p.high_percentile)):
        return "high"
    if value <= float(p.low_percentile):
        return "low"
    return "normal"


def _signal_from_states(risk: str, flow: str, valuation: str, liquidity: str) -> str:
    if risk == "high" or valuation == "overvalued" or flow == "exchange_inflow_pressure":
        return "risk_onchain_pressure"
    if valuation == "undervalued" or flow == "exchange_outflow_accumulation" or liquidity == "expanding":
        return "supportive_onchain"
    return "neutral"


def _normalized(series: pd.Series, p: OnChainParams) -> Optional[float]:
    valid = series.dropna()
    if len(valid) < 2:
        return None
    window = max(2, min(int(p.window), len(valid)))
    tail = valid.tail(window)
    low = tail.quantile(float(p.low_percentile) / 100.0)
    high = tail.quantile(float(p.high_percentile) / 100.0)
    if high == low:
        return None
    return float(((valid.iloc[-1] - low) / (high - low) * 100.0).clip(0.0, 100.0))


def _raw_to_frame(data: Any, extractor: Optional[ExtractorSpec]) -> ModuleResult[pd.DataFrame]:
    warnings: List[str] = []
    if extractor is not None and extractor.extractors:
        try:
            cols = {name: fn(data) for name, fn in extractor.extractors.items()}
            return ModuleResult.success(pd.DataFrame(cols), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("extractor_error", "extractor failed", details={"error": str(exc), "error_type": type(exc).__name__})
    if isinstance(data, pd.DataFrame):
        return ModuleResult.success(data.copy(), warnings=warnings)
    if isinstance(data, pd.Series):
        return ModuleResult.success(data.to_frame(name=data.name or "value").reset_index(drop=False), warnings=warnings)
    if isinstance(data, dict):
        try:
            if all(isinstance(v, IterableABC) and not isinstance(v, (str, bytes, dict)) for v in data.values()):
                return ModuleResult.success(pd.DataFrame(data), warnings=warnings)
            return ModuleResult.success(pd.DataFrame([data]), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("unsupported_input", "dict input could not be converted to DataFrame", details={"error": str(exc)})
    if isinstance(data, (list, tuple)):
        try:
            return ModuleResult.success(pd.DataFrame(data), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("unsupported_input", "sequence input could not be converted to DataFrame", details={"error": str(exc)})
    return ModuleResult.fail("unsupported_input", f"unsupported_input: {type(data).__name__}; provide DataFrame, Series, list, dict, or ExtractorSpec")


def _find_any_col(cols: Dict[str, Any], names: List[str]) -> Optional[Any]:
    for name in names:
        if not name:
            continue
        if name in cols:
            return cols[name]
        lower = str(name).lower()
        for key, col in cols.items():
            if key.lower() == lower:
                return col
    return None


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for value in series.tolist():
        num = _safe_float(value)
        out.append(num)
    return out


def _last_float(series: Optional[pd.Series]) -> Optional[float]:
    if series is None:
        return None
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return None
    return _safe_float(valid.iloc[-1])


def _safe_float(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except Exception:
        return None
    if not np.isfinite(num):
        return None
    return num


__all__ = ["OnChainParams", "OnChainReport", "normalize_onchain_input", "run_onchain_indicator", "ONCHAIN_INDICATORS"]
