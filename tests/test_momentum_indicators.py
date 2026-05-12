from pathlib import Path
import importlib
import math
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


MOMENTUM_MODULES = [
    "rsi",
    "stochastic_oscillator",
    "stochastic_fast",
    "stochastic_rsi",
    "cci",
    "cmo",
    "momentum",
    "roc",
    "rocp",
    "rocr",
    "rocr100",
    "williams_r",
    "ultimate_oscillator",
    "trix",
    "bop",
    "mfi",
    "awesome_oscillator",
    "accelerator_oscillator",
    "kst",
    "true_strength_index",
    "connors_rsi",
    "relative_vigor_index",
    "fisher_transform",
    "stochastic_momentum_index",
    "kdj",
    "demarker",
    "elder_ray",
    "qstick",
    "coppock_curve",
    "dpo",
    "chande_forecast_oscillator",
    "relative_momentum_index",
]


def _momentum_rows(mode="oscillating", n=360):
    rows = []
    for i in range(n):
        if mode == "up":
            base = 70.0 + i * 0.16
        elif mode == "down":
            base = 140.0 - i * 0.14
        elif mode == "flat":
            base = 100.0 + 0.15 * math.sin(i / 2.0)
        else:
            base = 100.0 + i * 0.03 + 4.0 * math.sin(i / 9.0) + 1.5 * math.sin(i / 3.0)
        close = base + 0.12 * math.sin(i / 5.0)
        open_ = close - 0.35 * math.sin(i / 4.0)
        high = max(open_, close) + 0.75 + (i % 5) * 0.03
        low = min(open_, close) - 0.72 - (i % 7) * 0.02
        rows.append(
            {
                "ts": f"2025-02-{(i % 28) + 1:02d}T00:00:00Z",
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1500.0 + i * 4.0 + 50.0 * abs(math.sin(i / 6.0)),
                "closed": True,
            }
        )
    return rows


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def test_all_momentum_modules_accept_records_and_dataframes():
    rows = _momentum_rows("oscillating")
    frame = pd.DataFrame(rows)
    for module_name in MOMENTUM_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.last_value is not None, module_name
            assert result.value.momentum_direction in {"bullish", "bearish", "neutral", "mixed", "unknown"}, module_name
            assert result.value.zone in {"overbought", "oversold", "neutral", "bullish", "bearish", "mixed", "unknown"}, module_name
            assert isinstance(result.value.last_values, dict), module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_momentum_modules_handle_up_down_and_flat_inputs():
    for mode in ("up", "down", "flat"):
        rows = _momentum_rows(mode)
        for module_name in MOMENTUM_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] == len(rows), module_name


def test_full_detail_returns_named_momentum_series():
    rows = _momentum_rows("oscillating")
    for module_name in ("rsi", "stochastic_oscillator", "mfi", "kst", "true_strength_index"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_invalid_missing_and_insufficient_momentum_inputs_fail_explicitly():
    from quant_strategy_tokenizer.indicators.bop import BOPRequest, run as run_bop
    from quant_strategy_tokenizer.indicators.mfi import MFIRequest, run as run_mfi
    from quant_strategy_tokenizer.indicators.rsi import RSIParams, RSIRequest, run as run_rsi

    invalid = run_rsi(RSIRequest(data=_momentum_rows(), params=RSIParams(window=0)))
    assert not invalid.ok
    assert invalid.failure.kind == "invalid_parameter"

    short = run_rsi(RSIRequest(data=_momentum_rows(n=5), params=RSIParams(window=14)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    missing_ohlc = run_bop(BOPRequest(data=[{"close": 100.0}, {"close": 101.0}]))
    assert not missing_ohlc.ok
    assert missing_ohlc.failure.kind == "missing_required_field"

    missing_volume = run_mfi(MFIRequest(data=[{"high": 2.0, "low": 1.0, "close": 1.5} for _ in range(20)]))
    assert not missing_volume.ok
    assert missing_volume.failure.kind == "missing_required_field"


def test_momentum_talib_backend_is_explicit_not_silent():
    from quant_strategy_tokenizer.indicators.rsi import RSIParams, RSIRequest, run as run_rsi

    result = run_rsi(RSIRequest(data=_momentum_rows(), params=RSIParams(backend="talib")))
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


def test_momentum_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.true_strength_index import (
        TrueStrengthIndexParams,
        TrueStrengthIndexRequest,
        run as run_tsi,
    )

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="true_strength_index", run_id="momentum-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_tsi(TrueStrengthIndexRequest(data=_momentum_rows(), params=TrueStrengthIndexParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_multiple_momentum_tokens():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.mfi import MFIParams, MFIRequest, run as run_mfi
    from quant_strategy_tokenizer.indicators.rsi import RSIParams, RSIRequest, run as run_rsi

    steps = [
        PipelineStep(
            name="rsi",
            input_key="initial",
            output_key="rsi_last",
            take="last_value",
            fn=lambda data: run_rsi(RSIRequest(data=data, params=RSIParams())),
        ),
        PipelineStep(
            name="mfi",
            input_key="initial",
            output_key="mfi_zone",
            take="zone",
            fn=lambda data: run_mfi(MFIRequest(data=data, params=MFIParams())),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "rsi_last": state.get("rsi_last"),
                    "mfi_zone": state.get("mfi_zone"),
                    "rsi_direction": state.get("rsi.momentum_direction"),
                }
            ),
        ),
    ]
    result = run_pipeline(_momentum_rows(), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["rsi_last"] is not None
    assert result.value.final_payload["mfi_zone"] in {"overbought", "oversold", "neutral"}
    assert result.value.final_payload["rsi_direction"] in {"bullish", "bearish", "neutral"}


if __name__ == "__main__":
    test_all_momentum_modules_accept_records_and_dataframes()
    test_momentum_modules_handle_up_down_and_flat_inputs()
    test_full_detail_returns_named_momentum_series()
    test_invalid_missing_and_insufficient_momentum_inputs_fail_explicitly()
    test_momentum_talib_backend_is_explicit_not_silent()
    test_momentum_output_dir_writes_standard_reports()
    test_pipeline_composes_multiple_momentum_tokens()
    print("momentum_indicator_tests_ok")
