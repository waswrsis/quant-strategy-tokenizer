from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib
import math
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DataFrameSpec, DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


ONCHAIN_MODULES = [
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
]


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def _onchain_rows(mode="normal_network", n=220, *, age_buckets=True, entity_rows=False):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        ts = (start + timedelta(days=t)).isoformat().replace("+00:00", "Z")
        price = 10000.0 + t * 20.0 + 200.0 * math.sin(t / 13.0)
        active = 850000.0 + t * 600.0 + 25000.0 * math.sin(t / 11.0)
        transactions = 300000.0 + t * 150.0 + 8000.0 * math.sin(t / 9.0)
        if mode == "high_activity":
            active *= 1.35
            transactions *= 1.30
        supply_total = 19000000.0 + t * 5.0
        if mode == "overvalued_mvrv":
            price *= 1.7
        market_cap = price * supply_total
        realized_cap = market_cap / (1.45 + 0.18 * math.sin(t / 31.0))
        if mode == "overvalued_mvrv":
            realized_cap = market_cap / 3.4
        transfer_volume = market_cap / (80.0 + 5.0 * math.sin(t / 10.0))
        exchange_in = 12000.0 + 600.0 * math.sin(t / 5.0) + t * 12.0
        exchange_out = 12500.0 + 500.0 * math.cos(t / 7.0) + t * 8.0
        if mode == "exchange_inflow_stress":
            exchange_in *= 2.2
            exchange_out *= 0.7
        if mode == "exchange_outflow_accumulation":
            exchange_in *= 0.7
            exchange_out *= 2.0
        stable_supply = 120000000000.0 + t * 20000000.0
        stable_exchange = 18000000000.0 + t * 2500000.0 + 100000000.0 * math.sin(t / 10.0)
        if mode == "stablecoin_expansion":
            stable_supply += t * 120000000.0
            stable_exchange += t * 20000000.0
        miner_reserve = 1800000.0 - t * 120.0 + 4000.0 * math.sin(t / 22.0)
        miner_flow = 500.0 + 80.0 * math.sin(t / 6.0)
        if mode == "miner_stress":
            miner_reserve -= t * 500.0
            miner_flow += t * 10.0
        staking_balance = 4000000.0 + t * 2500.0
        staking_withdrawals = 22000.0 + 900.0 * math.cos(t / 7.0)
        staking_deposits = 30000.0 + 1000.0 * math.sin(t / 8.0)
        if mode == "staking_withdrawal_stress":
            staking_withdrawals *= 2.5
            staking_deposits *= 0.6
            staking_balance -= t * 500.0
        sopr = 1.0 + 0.03 * math.sin(t / 12.0)
        if mode == "capitulation_sopr":
            sopr = 0.92 + 0.01 * math.sin(t / 8.0)
        if mode == "flat_invalid":
            transfer_volume = 0.0
            transactions = 0.0
            active = 0.0
            exchange_in = exchange_out = 0.0
            stable_supply = stable_exchange = 0.0
        base = {
            "ts": ts,
            "price": price,
            "market_cap": market_cap,
            "realized_cap": realized_cap,
            "transfer_volume": transfer_volume,
            "transaction_count": transactions,
            "active_addresses": active,
            "new_addresses": 70000.0 + t * 70.0 + 2000.0 * math.sin(t / 15.0),
            "exchange_inflow": exchange_in,
            "exchange_outflow": exchange_out,
            "exchange_balance": 2200000.0 - t * 700.0 + 10000.0 * math.sin(t / 16.0),
            "miner_reserve": miner_reserve,
            "miner_flow": miner_flow,
            "staking_deposits": staking_deposits,
            "staking_withdrawals": staking_withdrawals,
            "staking_balance": staking_balance,
            "supply": supply_total,
            "circulating_supply": supply_total,
            "stablecoin_supply": stable_supply,
            "stablecoin_exchange_balance": stable_exchange,
            "nvt": 80.0 + 5.0 * math.sin(t / 10.0),
            "mvrv": market_cap / realized_cap,
            "sopr": sopr,
            "realized_price": realized_cap / supply_total,
            "whale_balance": 8000000.0 + t * 1200.0,
            "retail_balance": 3000000.0 + t * 350.0,
            "gas_used": 100000000.0 + t * 1200000.0,
            "gas_price": 20.0 + 2.0 * math.sin(t / 8.0),
            "fees": 900.0 + 20.0 * math.sin(t / 5.0) + t * 0.8,
            "burned_fees": 500.0 + 12.0 * math.sin(t / 4.0) + t * 0.4,
            "chain": "btc",
            "asset": "BTC",
        }
        if entity_rows:
            for entity, frac in (("exchange", 0.55), ("whale", 0.30), ("retail", 0.15)):
                row = base.copy()
                row["entity"] = entity
                row["exchange_inflow"] *= frac
                row["exchange_outflow"] *= frac
                row["transfer_volume"] *= frac
                rows.append(row)
        elif age_buckets:
            for age, frac in ((30.0, 0.15), (90.0, 0.20), (180.0, 0.25), (365.0, 0.40)):
                row = base.copy()
                row["holder_age"] = age
                row["utxo_age"] = age
                row["age_bucket"] = str(int(age))
                row["supply"] = supply_total * frac
                rows.append(row)
        else:
            rows.append(base)
    return rows


def test_all_onchain_modules_accept_records_and_dataframe():
    rows = _onchain_rows()
    frame = pd.DataFrame(rows)
    for module_name in ONCHAIN_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.risk_state in {"low", "normal", "high", "unknown"}, module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_onchain_modules_handle_market_modes():
    modes = (
        "normal_network",
        "high_activity",
        "exchange_inflow_stress",
        "exchange_outflow_accumulation",
        "overvalued_mvrv",
        "capitulation_sopr",
        "stablecoin_expansion",
        "miner_stress",
        "staking_withdrawal_stress",
    )
    for mode in modes:
        rows = _onchain_rows(mode)
        for module_name in ONCHAIN_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] >= 80, module_name


def test_onchain_supports_age_bucket_and_entity_rows():
    for module_name in ("long_term_holder_supply_proxy", "short_term_holder_supply_proxy", "hodl_wave_proxy"):
        mod, params_cls, request_cls = _module_classes(module_name)
        result = mod.run(request_cls(data=_onchain_rows(age_buckets=True), params=params_cls()))
        assert result.ok, (module_name, result.failure)
        assert result.value.summary["input_kind"] == "age_bucket"
        assert result.value.diagnostics.get("proxy") is True

    mod, params_cls, request_cls = _module_classes("exchange_netflow")
    entity_result = mod.run(request_cls(data=_onchain_rows(age_buckets=False, entity_rows=True), params=params_cls()))
    assert entity_result.ok, entity_result.failure
    assert entity_result.value.summary["input_kind"] == "entity"


def test_onchain_respects_dataframe_spec_field_mapping():
    from quant_strategy_tokenizer.indicators.active_addresses import ActiveAddressesParams, ActiveAddressesRequest, run as run_active

    rows = []
    for row in _onchain_rows(n=90, age_buckets=False):
        rows.append({"time": row["ts"], "px": row["price"], "aa": row["active_addresses"]})
    spec = DataFrameSpec(ts_col="time", price_col="px")
    result = run_active(ActiveAddressesRequest(data=rows, params=ActiveAddressesParams(active_addresses_field="aa"), spec=spec))
    assert result.ok, result.failure
    assert result.value.used_fields["ts"] == "time"
    assert result.value.used_fields["price"] == "px"
    assert result.value.used_fields["active_addresses"] == "aa"


def test_full_detail_returns_named_onchain_series():
    for module_name in ("mvrv_zscore", "exchange_netflow", "stablecoin_liquidity_index", "onchain_risk_regime"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=_onchain_rows(), params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_onchain_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.onchain_risk_regime import OnchainRiskRegimeParams, OnchainRiskRegimeRequest, run as run_regime

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="onchain_risk_regime", run_id="onchain-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_regime(OnchainRiskRegimeRequest(data=_onchain_rows(), params=OnchainRiskRegimeParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail():
    from quant_strategy_tokenizer.indicators.active_addresses import ActiveAddressesParams, ActiveAddressesRequest, run as run_active
    from quant_strategy_tokenizer.indicators.exchange_netflow import ExchangeNetflowRequest, run as run_netflow
    from quant_strategy_tokenizer.indicators.fee_pressure import FeePressureRequest, run as run_fee
    from quant_strategy_tokenizer.indicators.hodl_wave_proxy import HodlWaveProxyRequest, run as run_hodl
    from quant_strategy_tokenizer.indicators.mvrv_zscore import MVRVZScoreRequest, run as run_mvrv
    from quant_strategy_tokenizer.indicators.nvt_ratio import NVTRatioRequest, run as run_nvt

    invalid_param = run_active(ActiveAddressesRequest(data=_onchain_rows(), params=ActiveAddressesParams(window=0)))
    assert not invalid_param.ok
    assert invalid_param.failure.kind == "invalid_parameter"

    missing_active = run_active(ActiveAddressesRequest(data=[{"ts": "2025-01-01T00:00:00Z", "price": 100.0}]))
    assert not missing_active.ok
    assert missing_active.failure.kind == "missing_required_field"

    missing_netflow = run_netflow(ExchangeNetflowRequest(data=[{"ts": "2025-01-01T00:00:00Z", "exchange_inflow": 1.0}]))
    assert not missing_netflow.ok
    assert missing_netflow.failure.kind == "missing_required_field"

    missing_age = run_hodl(HodlWaveProxyRequest(data=_onchain_rows(age_buckets=False)))
    assert not missing_age.ok
    assert missing_age.failure.kind == "missing_required_field"

    short_window = run_mvrv(MVRVZScoreRequest(data=_onchain_rows(n=5)))
    assert not short_window.ok
    assert short_window.failure.kind == "insufficient_data"

    zero_transfer = [{**row, "transfer_volume": 0.0, "nvt": None} for row in _onchain_rows()]
    nvt_res = run_nvt(NVTRatioRequest(data=zero_transfer))
    assert not nvt_res.ok
    assert nvt_res.failure.kind == "insufficient_data"

    fee_zero = [{**row, "transfer_volume": 0.0} for row in _onchain_rows()]
    fee_res = run_fee(FeePressureRequest(data=fee_zero))
    assert not fee_res.ok
    assert fee_res.failure.kind == "insufficient_data"


def test_pipeline_composes_onchain_tokens():
    from quant_strategy_tokenizer.indicators.exchange_netflow import ExchangeNetflowRequest, run as run_netflow
    from quant_strategy_tokenizer.indicators.mvrv_zscore import MVRVZScoreRequest, run as run_mvrv
    from quant_strategy_tokenizer.indicators.onchain_risk_regime import OnchainRiskRegimeRequest, run as run_risk
    from quant_strategy_tokenizer.indicators.stablecoin_liquidity_index import StablecoinLiquidityIndexRequest, run as run_stable

    rows = _onchain_rows("exchange_inflow_stress")
    result = run_pipeline(
        rows,
        [
            PipelineStep("mvrv", lambda data: run_mvrv(MVRVZScoreRequest(data=data)), input_key="initial", take="last_value", output_key="mvrv_z"),
            PipelineStep("netflow", lambda data: run_netflow(ExchangeNetflowRequest(data=data)), input_key="initial", take="last_value", output_key="exchange_netflow"),
            PipelineStep("stable", lambda data: run_stable(StablecoinLiquidityIndexRequest(data=data)), input_key="initial", take="last_value", output_key="stablecoin_liquidity"),
            PipelineStep("risk", lambda data: run_risk(OnchainRiskRegimeRequest(data=data)), input_key="initial", take="risk_state", output_key="onchain_risk"),
        ],
    )
    assert result.ok, result.failure
    assert {"mvrv_z", "exchange_netflow", "stablecoin_liquidity", "onchain_risk"}.issubset(result.value.values)


if __name__ == "__main__":
    test_all_onchain_modules_accept_records_and_dataframe()
    test_onchain_modules_handle_market_modes()
    test_onchain_supports_age_bucket_and_entity_rows()
    test_onchain_respects_dataframe_spec_field_mapping()
    test_full_detail_returns_named_onchain_series()
    test_onchain_output_dir_writes_standard_reports()
    test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail()
    test_pipeline_composes_onchain_tokens()
    print("onchain_indicator_tests_ok")
