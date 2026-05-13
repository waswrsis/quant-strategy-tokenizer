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


FUTURES_MODULES = [
    "funding_rate",
    "funding_rate_zscore",
    "funding_momentum",
    "funding_regime",
    "funding_crowding_score",
    "open_interest_change",
    "open_interest_roc",
    "open_interest_zscore",
    "price_oi_divergence",
    "oi_volume_ratio",
    "basis_rate",
    "basis_zscore",
    "basis_momentum",
    "premium_index",
    "mark_index_deviation",
    "perp_spot_deviation",
    "long_short_ratio",
    "long_short_ratio_zscore",
    "taker_buy_sell_ratio",
    "taker_flow_imbalance",
    "leverage_pressure_index",
    "liquidation_imbalance",
    "liquidation_pressure",
    "long_liquidation_ratio",
    "short_liquidation_ratio",
    "liquidation_cascade_risk",
    "derivatives_crowding_index",
    "perp_risk_regime",
    "futures_curve_pressure",
]

OPTIONS_MODULES = [
    "implied_volatility",
    "iv_rank",
    "iv_percentile",
    "iv_term_structure",
    "front_back_iv_spread",
    "put_call_iv_skew",
    "risk_reversal",
    "butterfly_skew",
    "smile_curvature",
    "atm_iv_skew",
    "put_call_volume_ratio",
    "put_call_open_interest_ratio",
    "option_volume_oi_ratio",
    "gamma_exposure",
    "delta_exposure",
    "vega_exposure",
    "theta_exposure",
    "dealer_gamma_proxy",
    "options_crowding_index",
    "volatility_risk_premium_proxy",
    "max_pain_proxy",
]


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def _perp_rows(mode="normal_perp", n=180):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        if mode == "rising_price_falling_oi":
            price = 100.0 + t * 0.45 + 1.0 * math.sin(t / 9.0)
            oi = 150000.0 - t * 420.0 + 2000.0 * math.sin(t / 12.0)
        elif mode == "negative_funding_stress":
            price = 130.0 - t * 0.22 + 1.5 * math.sin(t / 8.0)
            oi = 100000.0 + t * 500.0 + 5000.0 * math.sin(t / 16.0)
        else:
            price = 100.0 + t * 0.23 + 1.2 * math.sin(t / 7.0)
            oi = 100000.0 + t * 390.0 + 3500.0 * math.sin(t / 18.0)
        funding = 0.00008 + 0.00004 * math.sin(t / 9.0) + t * 0.0000004
        if mode == "positive_funding_crowded":
            funding = 0.00025 + t * 0.000001 + 0.00005 * math.sin(t / 11.0)
        elif mode == "negative_funding_stress":
            funding = -0.00022 - 0.00004 * math.sin(t / 10.0)
        mark = price * (1.0 + 0.001 * math.sin(t / 7.0))
        index = price * (1.0 + 0.0005 * math.sin(t / 11.0))
        spot = price * (1.0 - 0.0008 * math.cos(t / 13.0))
        if mode == "basis_expansion":
            mark = spot * (1.0 + 0.002 + t * 0.00002)
        long_liq = 1000.0 + max(0.0, math.sin(t / 8.0)) * 650.0 + t * 3.0
        short_liq = 900.0 + max(0.0, math.cos(t / 10.0)) * 550.0 + t * 2.0
        if mode == "liquidation_cascade":
            long_liq = 1500.0 + t * 35.0 + max(0.0, math.sin(t / 3.0)) * 3000.0
            short_liq = 800.0 + t * 8.0
        if mode == "flat_invalid":
            price = mark = index = spot = 100.0
            funding = 0.0
            oi = 100000.0
            long_liq = short_liq = 0.0
        rows.append(
            {
                "ts": (start + timedelta(hours=t)).isoformat().replace("+00:00", "Z"),
                "price": price,
                "mark_price": mark,
                "index_price": index,
                "spot_price": spot,
                "funding_rate": funding,
                "open_interest": oi,
                "basis": mark - spot,
                "premium": (mark - index) / index * 100.0,
                "long_short_ratio": 1.0 + 0.18 * math.sin(t / 17.0),
                "taker_buy_sell_ratio": 1.0 + 0.22 * math.sin(t / 6.0),
                "liquidation_long": long_liq,
                "liquidation_short": short_liq,
                "volume": 20000.0 + 1200.0 * math.sin(t / 8.0) + t * 25.0,
            }
        )
    return rows


def _option_rows(mode="options_put_skew", n=80):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        ts = start + timedelta(days=t)
        underlying = 100.0 + t * 0.25 + math.sin(t / 6.0)
        realized_vol = 0.24 + 0.02 * math.sin(t / 12.0)
        for dte in (30, 90):
            expiry = ts + timedelta(days=dte)
            for strike_mult in (0.90, 0.95, 1.00, 1.05, 1.10):
                strike = round(underlying * strike_mult, 2)
                moneyness = abs(strike / underlying - 1.0)
                for option_type in ("call", "put"):
                    if mode == "options_call_skew":
                        skew = 0.035 if option_type == "call" and strike > underlying else -0.005
                    else:
                        skew = 0.04 if option_type == "put" and strike < underlying else -0.005
                    term = -0.03 if mode == "iv_term_inversion" and dte == 90 else 0.02 if dte == 90 else 0.0
                    mark_iv = 0.34 + 0.05 * math.sin(t / 13.0) + moneyness * 0.65 + skew + term
                    delta = (0.55 - moneyness) if option_type == "call" else -(0.55 - moneyness)
                    rows.append(
                        {
                            "ts": ts.isoformat().replace("+00:00", "Z"),
                            "option_type": option_type,
                            "strike": strike,
                            "expiry": expiry.isoformat().replace("+00:00", "Z"),
                            "underlying_price": underlying,
                            "mark_iv": mark_iv,
                            "delta": delta,
                            "gamma": 0.02 + 0.01 * (1.0 - moneyness),
                            "vega": 0.12 + 0.03 * (1.0 - moneyness),
                            "theta": -0.02 - 0.01 * moneyness,
                            "volume": 100.0 + 20.0 * math.sin(t / 9.0) + 80.0 * (1.0 - moneyness),
                            "open_interest": 500.0 + 100.0 * (1.0 - moneyness) + t * 2.0,
                            "realized_volatility": realized_vol,
                        }
                    )
    return rows


def test_all_futures_derivative_modules_accept_records_and_dataframe():
    rows = _perp_rows()
    frame = pd.DataFrame(rows)
    for module_name in FUTURES_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.risk_state in {"low", "normal", "high", "extreme", "unknown"}, module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_futures_derivatives_handle_multiple_market_modes():
    for mode in (
        "normal_perp",
        "positive_funding_crowded",
        "negative_funding_stress",
        "rising_price_rising_oi",
        "rising_price_falling_oi",
        "basis_expansion",
        "liquidation_cascade",
    ):
        rows = _perp_rows(mode)
        for module_name in FUTURES_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] >= 80, module_name


def test_all_option_derivative_modules_accept_records_and_dataframe():
    rows = _option_rows()
    frame = pd.DataFrame(rows)
    for module_name in OPTIONS_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.summary["input_kind"] == "options", module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_options_derivatives_handle_skew_and_term_structure_modes():
    for mode in ("options_call_skew", "options_put_skew", "iv_term_inversion"):
        rows = _option_rows(mode)
        for module_name in OPTIONS_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            if module_name in {"dealer_gamma_proxy", "volatility_risk_premium_proxy", "max_pain_proxy"}:
                assert result.value.diagnostics.get("proxy") is True, module_name


def test_derivatives_respect_dataframe_spec_field_mapping():
    from quant_strategy_tokenizer.indicators.funding_rate_zscore import FundingRateZScoreParams, FundingRateZScoreRequest, run as run_funding

    rows = []
    for row in _perp_rows(n=90):
        rows.append({"time": row["ts"], "px": row["price"], "vol": row["volume"], "fund": row["funding_rate"]})
    spec = DataFrameSpec(ts_col="time", price_col="px", volume_col="vol")
    result = run_funding(FundingRateZScoreRequest(data=rows, params=FundingRateZScoreParams(funding_rate_field="fund"), spec=spec))
    assert result.ok, result.failure
    assert result.value.used_fields["ts"] == "time"
    assert result.value.used_fields["price"] == "px"
    assert result.value.used_fields["funding_rate"] == "fund"


def test_full_detail_returns_derivatives_series():
    for module_name, rows in (("funding_rate_zscore", _perp_rows()), ("put_call_iv_skew", _option_rows())):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_output_dir_writes_redacted_derivatives_reports():
    from quant_strategy_tokenizer.indicators.options_crowding_index import OptionsCrowdingIndexParams, OptionsCrowdingIndexRequest, run as run_options_crowding

    with tempfile.TemporaryDirectory() as td:
        ctx = ModuleRunContext(module="options_crowding_index", detail_level=DetailLevel.FULL, output_dir=td, run_id="derivatives-smoke")
        result = run_options_crowding(OptionsCrowdingIndexRequest(data=_option_rows(), params=OptionsCrowdingIndexParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail():
    from quant_strategy_tokenizer.indicators.funding_rate import FundingRateParams, FundingRateRequest, run as run_funding
    from quant_strategy_tokenizer.indicators.gamma_exposure import GammaExposureRequest, run as run_gamma
    from quant_strategy_tokenizer.indicators.liquidation_pressure import LiquidationPressureRequest, run as run_liq
    from quant_strategy_tokenizer.indicators.open_interest_change import OpenInterestChangeRequest, run as run_oi
    from quant_strategy_tokenizer.indicators.option_volume_oi_ratio import OptionVolumeOIRatioRequest, run as run_option_volume_oi

    invalid_param = run_funding(FundingRateRequest(data=_perp_rows(), params=FundingRateParams(window=0)))
    assert not invalid_param.ok
    assert invalid_param.failure.kind == "invalid_parameter"

    missing_funding = run_funding(FundingRateRequest(data=[{"ts": "2025-01-01T00:00:00Z", "price": 100.0}]))
    assert not missing_funding.ok
    assert missing_funding.failure.kind == "missing_required_field"

    missing_oi = run_oi(OpenInterestChangeRequest(data=[{"ts": "2025-01-01T00:00:00Z", "price": 100.0}]))
    assert not missing_oi.ok
    assert missing_oi.failure.kind == "missing_required_field"

    missing_liquidation = run_liq(LiquidationPressureRequest(data=_perp_rows()[0:10]))
    assert not missing_liquidation.ok
    assert missing_liquidation.failure.kind in {"missing_required_field", "insufficient_data"}

    short_window = run_funding(FundingRateRequest(data=_perp_rows(n=1)))
    assert not short_window.ok
    assert short_window.failure.kind == "insufficient_data"

    option_rows = _option_rows()
    missing_gamma = [{k: v for k, v in row.items() if k != "gamma"} for row in option_rows]
    gamma_res = run_gamma(GammaExposureRequest(data=missing_gamma))
    assert not gamma_res.ok
    assert gamma_res.failure.kind == "missing_required_field"

    zero_oi = [{**row, "open_interest": 0.0} for row in option_rows]
    option_oi_res = run_option_volume_oi(OptionVolumeOIRatioRequest(data=zero_oi))
    assert not option_oi_res.ok
    assert option_oi_res.failure.kind == "insufficient_data"


def test_pipeline_can_combine_futures_and_options_derivative_tokens():
    from quant_strategy_tokenizer.indicators.basis_rate import BasisRateRequest, run as run_basis
    from quant_strategy_tokenizer.indicators.funding_rate_zscore import FundingRateZScoreRequest, run as run_funding
    from quant_strategy_tokenizer.indicators.liquidation_pressure import LiquidationPressureRequest, run as run_liq
    from quant_strategy_tokenizer.indicators.open_interest_change import OpenInterestChangeRequest, run as run_oi
    from quant_strategy_tokenizer.indicators.options_crowding_index import OptionsCrowdingIndexRequest, run as run_options_crowding
    from quant_strategy_tokenizer.indicators.put_call_iv_skew import PutCallIVSkewRequest, run as run_skew

    futures_rows = _perp_rows()
    futures_pipeline = run_pipeline(
        futures_rows,
        [
            PipelineStep("funding", lambda data: run_funding(FundingRateZScoreRequest(data=data)), input_key="initial", take="last_value", output_key="funding_z"),
            PipelineStep("oi", lambda data: run_oi(OpenInterestChangeRequest(data=data)), input_key="initial", take="last_value", output_key="oi_change"),
            PipelineStep("basis", lambda data: run_basis(BasisRateRequest(data=data)), input_key="initial", take="last_value", output_key="basis_rate"),
            PipelineStep("liquidation", lambda data: run_liq(LiquidationPressureRequest(data=data)), input_key="initial", take="last_value", output_key="liquidation_pressure"),
        ],
    )
    assert futures_pipeline.ok, futures_pipeline.failure
    assert {"funding_z", "oi_change", "basis_rate", "liquidation_pressure"}.issubset(futures_pipeline.value.values)

    option_rows = _option_rows()
    option_pipeline = run_pipeline(
        option_rows,
        [
            PipelineStep("skew", lambda data: run_skew(PutCallIVSkewRequest(data=data)), input_key="initial", take="last_value", output_key="put_call_iv_skew"),
            PipelineStep("crowding", lambda data: run_options_crowding(OptionsCrowdingIndexRequest(data=data)), input_key="initial", take="last_value", output_key="options_crowding"),
        ],
    )
    assert option_pipeline.ok, option_pipeline.failure
    assert {"put_call_iv_skew", "options_crowding"}.issubset(option_pipeline.value.values)


if __name__ == "__main__":
    test_all_futures_derivative_modules_accept_records_and_dataframe()
    test_futures_derivatives_handle_multiple_market_modes()
    test_all_option_derivative_modules_accept_records_and_dataframe()
    test_options_derivatives_handle_skew_and_term_structure_modes()
    test_derivatives_respect_dataframe_spec_field_mapping()
    test_full_detail_returns_derivatives_series()
    test_output_dir_writes_redacted_derivatives_reports()
    test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail()
    test_pipeline_can_combine_futures_and_options_derivative_tokens()
    print("derivatives_indicator_tests_ok")
