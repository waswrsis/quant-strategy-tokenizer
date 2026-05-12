from pathlib import Path
import importlib
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


TREND_MODULES = [
    "sma",
    "wma",
    "smma",
    "dema",
    "tema",
    "trima",
    "t3",
    "hma",
    "kama",
    "zlema",
    "mcginley_dynamic",
    "vwma",
    "macd",
    "ppo",
    "apo",
    "adx",
    "adxr",
    "dmi",
    "aroon",
    "aroon_oscillator",
    "vortex",
    "parabolic_sar",
    "supertrend",
    "donchian_channel",
    "keltner_channel",
    "chandelier_exit",
    "atr_trailing_stop",
    "ichimoku_cloud",
    "alligator",
    "ma_cross",
    "ma_ribbon",
    "gmma",
    "linear_regression",
    "linear_regression_slope",
    "linear_regression_angle",
    "linear_regression_r2",
    "least_squares_moving_average",
    "time_series_forecast",
    "mama",
    "ht_trendline",
    "ht_trendmode",
    "ht_sinewave",
    "ht_phasor",
    "ht_dominant_cycle_period",
    "ht_dominant_cycle_phase",
    "trend_strength_index",
    "chande_trend_meter",
]


def _trend_rows(mode="up", n=260):
    rows = []
    for i in range(n):
        if mode == "down":
            base = 180.0 - i * 0.25
        elif mode == "flat":
            base = 100.0 + ((i % 12) - 6) * 0.03
        elif mode == "reversal":
            base = 150.0 - i * 0.22 if i < n // 2 else 121.0 + (i - n // 2) * 0.34
        else:
            base = 80.0 + i * 0.28
        close = base + ((i % 7) - 3) * 0.04
        rows.append(
            {
                "ts": f"2025-01-{(i % 28) + 1:02d}T00:00:00Z",
                "open": close - 0.18,
                "high": close + 0.52,
                "low": close - 0.49,
                "close": close,
                "volume": 1000.0 + i * 3.0,
                "closed": True,
            }
        )
    return rows


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = next(cls for name, cls in vars(mod).items() if name.endswith("Params") and name != "TrendParams")
    request_cls = next(cls for name, cls in vars(mod).items() if name.endswith("Request"))
    return mod, params_cls, request_cls


def test_all_trend_modules_accept_records_and_dataframes():
    rows = _trend_rows("up")
    frame = pd.DataFrame(rows)
    for module_name in TREND_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.last_value is not None, module_name
            assert result.value.trend_direction in {
                "bullish",
                "bearish",
                "neutral",
                "mixed",
                "cycle",
                "trend",
                "unknown",
            }, module_name
            assert isinstance(result.value.last_values, dict), module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_trend_modules_handle_down_flat_and_reversal_inputs():
    for mode in ("down", "flat", "reversal"):
        rows = _trend_rows(mode)
        for module_name in TREND_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] == len(rows), module_name


def test_full_detail_returns_named_series():
    rows = _trend_rows("reversal")
    for module_name in ("sma", "macd", "ichimoku_cloud", "ht_trendline"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_invalid_missing_and_insufficient_inputs_fail_explicitly():
    from quant_strategy_tokenizer.indicators.sma import SMAParams, SMARequest, run as run_sma
    from quant_strategy_tokenizer.indicators.supertrend import SupertrendRequest, run as run_supertrend

    invalid = run_sma(SMARequest(data=_trend_rows("up"), params=SMAParams(window=0)))
    assert not invalid.ok
    assert invalid.failure.kind == "invalid_parameter"

    short = run_sma(SMARequest(data=_trend_rows("up", n=8), params=SMAParams(window=20)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    missing = run_supertrend(SupertrendRequest(data=[{"close": 100.0}, {"close": 101.0}]))
    assert not missing.ok
    assert missing.failure.kind == "missing_required_field"


def test_vwma_accepts_price_volume_without_ohlc_fields():
    from quant_strategy_tokenizer.indicators.vwma import VWMAParams, VWMARequest, run as run_vwma

    rows = [{"close": 100.0 + i, "volume": 10.0 + i} for i in range(40)]
    result = run_vwma(VWMARequest(data=rows, params=VWMAParams(window=10)))
    assert result.ok, result.failure
    assert result.value.used_fields == {"close": "close", "volume": "volume"}
    assert result.value.last_value is not None


def test_talib_backend_is_explicit_not_silent():
    from quant_strategy_tokenizer.indicators.sma import SMAParams, SMARequest, run as run_sma

    result = run_sma(SMARequest(data=_trend_rows("up"), params=SMAParams(backend="talib")))
    try:
        import talib  # noqa: F401

        talib_available = True
    except Exception:
        talib_available = False
    if talib_available:
        assert result.ok, result.failure
        assert result.value.summary["backend"] == "talib"
    else:
        assert not result.ok
        assert result.failure.kind == "unavailable_backend"


def test_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.macd import MACDParams, MACDRequest, run as run_macd

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="macd", run_id="trend-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_macd(MACDRequest(data=_trend_rows("up"), params=MACDParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_multiple_trend_tokens():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.macd import MACDParams, MACDRequest, run as run_macd
    from quant_strategy_tokenizer.indicators.sma import SMAParams, SMARequest, run as run_sma

    steps = [
        PipelineStep(
            name="sma",
            input_key="initial",
            output_key="sma_last",
            take="last_value",
            fn=lambda data: run_sma(SMARequest(data=data, params=SMAParams(window=20))),
        ),
        PipelineStep(
            name="macd",
            input_key="initial",
            output_key="macd_hist",
            take="last_values.histogram",
            fn=lambda data: run_macd(MACDRequest(data=data, params=MACDParams())),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "sma_last": state.get("sma_last"),
                    "macd_hist": state.get("macd_hist"),
                    "macd_direction": state.get("macd.trend_direction"),
                }
            ),
        ),
    ]
    result = run_pipeline(_trend_rows("up"), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["sma_last"] is not None
    assert result.value.final_payload["macd_hist"] is not None
    assert result.value.final_payload["macd_direction"] in {"bullish", "bearish", "neutral"}


if __name__ == "__main__":
    test_all_trend_modules_accept_records_and_dataframes()
    test_trend_modules_handle_down_flat_and_reversal_inputs()
    test_full_detail_returns_named_series()
    test_invalid_missing_and_insufficient_inputs_fail_explicitly()
    test_vwma_accepts_price_volume_without_ohlc_fields()
    test_talib_backend_is_explicit_not_silent()
    test_output_dir_writes_standard_reports()
    test_pipeline_composes_multiple_trend_tokens()
    print("trend_indicator_tests_ok")
