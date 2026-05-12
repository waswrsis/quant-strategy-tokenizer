from pathlib import Path
import importlib
import math
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


VOLATILITY_MODULES = [
    "true_range",
    "natr",
    "high_low_range",
    "rolling_range",
    "average_range",
    "gap_range",
    "range_percent",
    "range_expansion",
    "rolling_stddev",
    "rolling_variance",
    "historical_volatility",
    "realized_volatility",
    "ewma_volatility",
    "parkinson_volatility",
    "garman_klass_volatility",
    "rogers_satchell_volatility",
    "yang_zhang_volatility",
    "downside_volatility",
    "volatility_of_volatility",
    "bollinger_bands",
    "bollinger_bandwidth",
    "percent_b",
    "zscore",
    "zscore_bands",
    "ttm_squeeze",
    "bollinger_keltner_squeeze",
    "chaikin_volatility",
    "mass_index",
    "ulcer_index",
    "relative_volatility_index",
    "inertia",
    "vertical_horizontal_filter",
    "volatility_ratio",
    "volatility_regime",
]


def _volatility_rows(mode="calm", n=360):
    rows = []
    for i in range(n):
        if mode == "high_vol":
            amp = 2.6 + 1.4 * abs(math.sin(i / 5.0))
            trend = 0.05 * i
        elif mode == "expanding":
            amp = 0.4 + 0.012 * i
            trend = 0.025 * i
        elif mode == "contracting":
            amp = max(0.35, 4.0 - 0.010 * i)
            trend = 0.02 * i
        elif mode == "gap":
            amp = 1.0 + 0.3 * abs(math.sin(i / 8.0))
            trend = 0.02 * i + (4.0 if i % 45 == 0 else 0.0)
        elif mode == "flat":
            amp = 0.35 + 0.05 * abs(math.sin(i / 6.0))
            trend = 0.08 * math.sin(i / 12.0)
        else:
            amp = 0.75 + 0.25 * abs(math.sin(i / 9.0))
            trend = 0.02 * i
        base = 100.0 + trend + 1.2 * math.sin(i / 13.0)
        close = base + 0.12 * math.sin(i / 3.0)
        open_ = close - 0.25 * math.sin(i / 4.0)
        high = max(open_, close) + amp
        low = min(open_, close) - amp * (0.92 + 0.08 * abs(math.cos(i / 7.0)))
        rows.append(
            {
                "ts": f"2025-03-{(i % 28) + 1:02d}T00:00:00Z",
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1200.0 + i * 3.0,
                "closed": True,
            }
        )
    return rows


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def test_all_volatility_modules_accept_records_and_dataframes():
    rows = _volatility_rows("calm")
    frame = pd.DataFrame(rows)
    for module_name in VOLATILITY_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.volatility_direction in {"expanding", "contracting", "stable", "unknown"}, module_name
            assert result.value.volatility_level in {"low", "normal", "high", "extreme", "unknown"}, module_name
            assert isinstance(result.value.last_values, dict), module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_volatility_modules_handle_multiple_regimes():
    for mode in ("calm", "high_vol", "expanding", "contracting", "gap", "flat"):
        rows = _volatility_rows(mode)
        for module_name in VOLATILITY_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] == len(rows), module_name


def test_full_detail_returns_named_volatility_series():
    rows = _volatility_rows("expanding")
    for module_name in ("natr", "bollinger_bands", "ttm_squeeze", "volatility_regime", "yang_zhang_volatility"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_invalid_missing_insufficient_and_zero_range_fail_explicitly():
    from quant_strategy_tokenizer.indicators.natr import NATRRequest, run as run_natr
    from quant_strategy_tokenizer.indicators.percent_b import PercentBRequest, run as run_percent_b
    from quant_strategy_tokenizer.indicators.rolling_stddev import RollingStddevParams, RollingStddevRequest, run as run_stddev

    invalid = run_stddev(RollingStddevRequest(data=_volatility_rows(), params=RollingStddevParams(window=0)))
    assert not invalid.ok
    assert invalid.failure.kind == "invalid_parameter"

    missing = run_natr(NATRRequest(data=[{"close": 100.0}, {"close": 101.0}]))
    assert not missing.ok
    assert missing.failure.kind == "missing_required_field"

    short = run_stddev(RollingStddevRequest(data=_volatility_rows(n=5), params=RollingStddevParams(window=20)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    zero_range = [{"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0} for _ in range(80)]
    flat = run_percent_b(PercentBRequest(data=zero_range))
    assert not flat.ok
    assert flat.failure.kind == "insufficient_data"


def test_volatility_talib_backend_is_explicit_not_silent():
    from quant_strategy_tokenizer.indicators.natr import NATRParams, NATRRequest, run as run_natr

    result = run_natr(NATRRequest(data=_volatility_rows(), params=NATRParams(backend="talib")))
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


def test_volatility_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.volatility_regime import (
        VolatilityRegimeParams,
        VolatilityRegimeRequest,
        run as run_regime,
    )

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="volatility_regime", run_id="vol-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_regime(VolatilityRegimeRequest(data=_volatility_rows(), params=VolatilityRegimeParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_atr_bandwidth_and_regime_tokens():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.atr import ATRParams, ATRRequest, run as run_atr
    from quant_strategy_tokenizer.indicators.bollinger_bandwidth import (
        BollingerBandwidthParams,
        BollingerBandwidthRequest,
        run as run_bandwidth,
    )
    from quant_strategy_tokenizer.indicators.volatility_regime import (
        VolatilityRegimeParams,
        VolatilityRegimeRequest,
        run as run_regime,
    )

    steps = [
        PipelineStep(
            name="atr",
            input_key="initial",
            output_key="atr_last",
            take="last_value",
            fn=lambda data: run_atr(ATRRequest(data=data, params=ATRParams())),
        ),
        PipelineStep(
            name="bandwidth",
            input_key="initial",
            output_key="bandwidth_last",
            take="last_value",
            fn=lambda data: run_bandwidth(BollingerBandwidthRequest(data=data, params=BollingerBandwidthParams())),
        ),
        PipelineStep(
            name="regime",
            input_key="initial",
            output_key="vol_regime",
            take="regime",
            fn=lambda data: run_regime(VolatilityRegimeRequest(data=data, params=VolatilityRegimeParams())),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "atr": state.get("atr_last"),
                    "bandwidth": state.get("bandwidth_last"),
                    "regime": state.get("vol_regime"),
                }
            ),
        ),
    ]
    result = run_pipeline(_volatility_rows("high_vol"), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["atr"] is not None
    assert result.value.final_payload["bandwidth"] is not None
    assert result.value.final_payload["regime"] in {"low", "normal", "high", "extreme", "unknown"}


def test_existing_volatility_related_modules_keep_compatible_fields():
    from quant_strategy_tokenizer.indicators.atr import ATRRequest, run as run_atr
    from quant_strategy_tokenizer.indicators.chop import CHOPRequest, run as run_chop
    from quant_strategy_tokenizer.indicators.spike import SpikeRequest, run as run_spike

    for result in (run_atr(ATRRequest(data=_volatility_rows())), run_chop(CHOPRequest(data=_volatility_rows())), run_spike(SpikeRequest(data=_volatility_rows("gap")))):
        assert result.ok, result.failure
        assert result.value.last_value is not None
        assert result.value.indicator in {"atr", "chop", "spike"}
        assert isinstance(result.value.last_values, dict)


if __name__ == "__main__":
    test_all_volatility_modules_accept_records_and_dataframes()
    test_volatility_modules_handle_multiple_regimes()
    test_full_detail_returns_named_volatility_series()
    test_invalid_missing_insufficient_and_zero_range_fail_explicitly()
    test_volatility_talib_backend_is_explicit_not_silent()
    test_volatility_output_dir_writes_standard_reports()
    test_pipeline_composes_atr_bandwidth_and_regime_tokens()
    test_existing_volatility_related_modules_keep_compatible_fields()
    print("volatility_indicator_tests_ok")
