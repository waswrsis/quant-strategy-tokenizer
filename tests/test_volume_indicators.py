from pathlib import Path
import importlib
import math
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


VOLUME_MODULES = [
    "volume_sma",
    "volume_ema",
    "volume_roc",
    "volume_zscore",
    "relative_volume",
    "volume_percentile",
    "volume_spike",
    "volume_dry_up",
    "volume_trend",
    "volume_oscillator",
    "obv",
    "accumulation_distribution_line",
    "chaikin_money_flow",
    "chaikin_oscillator",
    "volume_price_trend",
    "positive_volume_index",
    "negative_volume_index",
    "force_index",
    "ease_of_movement",
    "intraday_intensity",
    "money_flow_volume",
    "klinger_oscillator",
    "volume_flow_indicator",
    "demand_index",
    "signed_volume_proxy",
    "cumulative_signed_volume_proxy",
    "price_volume_divergence",
    "volume_confirmation",
]


def _volume_rows(mode="normal", n=360):
    rows = []
    for i in range(n):
        if mode == "high_volume":
            volume = 2500.0 + i * 8.0 + 500.0 * abs(math.sin(i / 7.0))
            drift = 0.04 * i
        elif mode == "dry_up":
            volume = max(80.0, 2200.0 - i * 5.0) + 40.0 * abs(math.sin(i / 9.0))
            drift = 0.015 * i
        elif mode == "expanding_volume":
            volume = 500.0 + i * 12.0 + 150.0 * abs(math.sin(i / 5.0))
            drift = 0.03 * i
        elif mode == "distribution":
            volume = 1300.0 + i * 5.0 + 120.0 * abs(math.sin(i / 8.0))
            drift = -0.035 * i
        elif mode == "accumulation":
            volume = 1300.0 + i * 5.0 + 120.0 * abs(math.sin(i / 8.0))
            drift = 0.035 * i
        elif mode == "flat_price":
            volume = 1200.0 + 160.0 * abs(math.sin(i / 6.0)) + (i % 11) * 4.0
            drift = 0.06 * math.sin(i / 10.0)
        else:
            volume = 1200.0 + i * 2.5 + 80.0 * abs(math.sin(i / 8.0))
            drift = 0.02 * i
        base = 100.0 + drift + 1.0 * math.sin(i / 13.0)
        close = base + 0.12 * math.sin(i / 3.0)
        open_ = close - 0.25 * math.sin(i / 4.0)
        high = max(open_, close) + 0.9 + 0.2 * abs(math.sin(i / 6.0))
        low = min(open_, close) - 0.9 - 0.2 * abs(math.cos(i / 7.0))
        rows.append(
            {
                "ts": f"2025-04-{(i % 28) + 1:02d}T00:00:00Z",
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "closed": True,
            }
        )
    return rows


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def test_all_volume_modules_accept_records_and_dataframes():
    rows = _volume_rows("normal")
    frame = pd.DataFrame(rows)
    for module_name in VOLUME_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.volume_direction in {"increasing", "decreasing", "stable", "mixed", "unknown"}, module_name
            assert result.value.volume_level in {"dry_up", "low", "normal", "high", "extreme", "unknown"}, module_name
            assert result.value.flow_direction in {"accumulation", "distribution", "neutral", "unknown"}, module_name
            assert isinstance(result.value.last_values, dict), module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_volume_modules_handle_multiple_regimes():
    for mode in ("normal", "high_volume", "dry_up", "expanding_volume", "distribution", "accumulation", "flat_price"):
        rows = _volume_rows(mode)
        for module_name in VOLUME_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] == len(rows), module_name


def test_volume_only_tokens_accept_simple_sequences():
    from quant_strategy_tokenizer.indicators.volume_sma import VolumeSMAParams, VolumeSMARequest, run as run_volume_sma

    result = run_volume_sma(VolumeSMARequest(data=[100, 120, 140, 130, 150], params=VolumeSMAParams(window=3)))
    assert result.ok, result.failure
    assert result.value.last_value is not None
    assert "volume field was inferred from value column" in result.value.warnings


def test_full_detail_returns_named_volume_series():
    rows = _volume_rows("accumulation")
    for module_name in ("relative_volume", "obv", "chaikin_money_flow", "klinger_oscillator", "volume_confirmation"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_invalid_missing_insufficient_and_zero_volume_fail_explicitly():
    from quant_strategy_tokenizer.indicators.chaikin_money_flow import ChaikinMoneyFlowRequest, run as run_cmf
    from quant_strategy_tokenizer.indicators.obv import OBVRequest, run as run_obv
    from quant_strategy_tokenizer.indicators.volume_sma import VolumeSMAParams, VolumeSMARequest, run as run_volume_sma

    invalid = run_volume_sma(VolumeSMARequest(data=_volume_rows(), params=VolumeSMAParams(window=0)))
    assert not invalid.ok
    assert invalid.failure.kind == "invalid_parameter"

    missing_volume = run_obv(OBVRequest(data=[{"close": 100.0}, {"close": 101.0}]))
    assert not missing_volume.ok
    assert missing_volume.failure.kind == "missing_required_field"

    missing_ohlc = run_cmf(ChaikinMoneyFlowRequest(data=[{"close": 100.0, "volume": 10.0} for _ in range(30)]))
    assert not missing_ohlc.ok
    assert missing_ohlc.failure.kind == "missing_required_field"

    short = run_volume_sma(VolumeSMARequest(data=_volume_rows(n=5), params=VolumeSMAParams(window=20)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    zero_volume = run_obv(OBVRequest(data=[{"close": 100.0 + i, "volume": 0.0} for i in range(40)]))
    assert not zero_volume.ok
    assert zero_volume.failure.kind == "invalid_numeric"


def test_volume_talib_backend_is_explicit_not_silent():
    from quant_strategy_tokenizer.indicators.obv import OBVParams, OBVRequest, run as run_obv

    result = run_obv(OBVRequest(data=_volume_rows(), params=OBVParams(backend="talib")))
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


def test_volume_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.volume_confirmation import (
        VolumeConfirmationParams,
        VolumeConfirmationRequest,
        run as run_confirmation,
    )

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="volume_confirmation", run_id="volume-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_confirmation(VolumeConfirmationRequest(data=_volume_rows(), params=VolumeConfirmationParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_relative_volume_obv_and_confirmation():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.obv import OBVParams, OBVRequest, run as run_obv
    from quant_strategy_tokenizer.indicators.relative_volume import RelativeVolumeParams, RelativeVolumeRequest, run as run_relative_volume
    from quant_strategy_tokenizer.indicators.volume_confirmation import (
        VolumeConfirmationParams,
        VolumeConfirmationRequest,
        run as run_confirmation,
    )

    steps = [
        PipelineStep(
            name="relative_volume",
            input_key="initial",
            output_key="rv_last",
            take="last_value",
            fn=lambda data: run_relative_volume(RelativeVolumeRequest(data=data, params=RelativeVolumeParams())),
        ),
        PipelineStep(
            name="obv",
            input_key="initial",
            output_key="obv_flow",
            take="flow_direction",
            fn=lambda data: run_obv(OBVRequest(data=data, params=OBVParams())),
        ),
        PipelineStep(
            name="confirmation",
            input_key="initial",
            output_key="confirmation_signal",
            take="signal",
            fn=lambda data: run_confirmation(VolumeConfirmationRequest(data=data, params=VolumeConfirmationParams())),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "relative_volume": state.get("rv_last"),
                    "obv_flow": state.get("obv_flow"),
                    "confirmation": state.get("confirmation_signal"),
                }
            ),
        ),
    ]
    result = run_pipeline(_volume_rows("accumulation"), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["relative_volume"] is not None
    assert result.value.final_payload["obv_flow"] in {"accumulation", "distribution", "neutral", "unknown"}
    assert result.value.final_payload["confirmation"] in {"confirmed", "distribution_confirmed", "unconfirmed"}


if __name__ == "__main__":
    test_all_volume_modules_accept_records_and_dataframes()
    test_volume_modules_handle_multiple_regimes()
    test_volume_only_tokens_accept_simple_sequences()
    test_full_detail_returns_named_volume_series()
    test_invalid_missing_insufficient_and_zero_volume_fail_explicitly()
    test_volume_talib_backend_is_explicit_not_silent()
    test_volume_output_dir_writes_standard_reports()
    test_pipeline_composes_relative_volume_obv_and_confirmation()
    print("volume_indicator_tests_ok")
