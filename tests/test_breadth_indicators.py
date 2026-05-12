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


BREADTH_MODULES = [
    "advance_decline_line",
    "advance_decline_ratio",
    "advance_decline_percent",
    "net_advances",
    "absolute_breadth_index",
    "breadth_thrust",
    "mcclellan_oscillator",
    "mcclellan_summation_index",
    "mcclellan_ratio_adjusted_oscillator",
    "new_highs",
    "new_lows",
    "net_new_highs",
    "new_high_new_low_ratio",
    "high_low_index",
    "cumulative_new_highs_new_lows",
    "percent_positive_return",
    "percent_above_ma",
    "percent_above_ema",
    "percent_above_threshold",
    "percent_near_high",
    "percent_near_low",
    "up_down_volume_ratio",
    "up_down_volume_line",
    "volume_advance_decline_percent",
    "arms_index",
    "trin",
    "volume_breadth_thrust",
    "cross_sectional_dispersion",
    "cross_sectional_correlation_proxy",
    "equal_weighted_return",
    "cap_weighted_breadth",
    "breadth_momentum",
    "breadth_regime",
    "index_breadth_divergence",
    "breadth_confirmation",
    "breadth_freeze_pressure",
]

PANEL_ONLY = {
    "percent_above_ma",
    "percent_above_ema",
    "percent_above_threshold",
    "percent_near_high",
    "percent_near_low",
    "cross_sectional_dispersion",
    "cross_sectional_correlation_proxy",
    "equal_weighted_return",
    "cap_weighted_breadth",
}

VOLUME_BREADTH = {
    "up_down_volume_ratio",
    "up_down_volume_line",
    "volume_advance_decline_percent",
    "arms_index",
    "trin",
    "volume_breadth_thrust",
}

INDEX_BREADTH = {"index_breadth_divergence", "breadth_confirmation"}


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def _breadth_rows(mode="broad_up", n=180, symbols=18):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        ts = (start + timedelta(days=t)).isoformat().replace("+00:00", "Z")
        if mode == "broad_down":
            index_close = 160.0 - t * 0.11
        elif mode == "divergence":
            index_close = 100.0 + t * 0.12
        elif mode == "narrow_rally":
            index_close = 100.0 + t * 0.10
        else:
            index_close = 100.0 + t * 0.04 + 1.0 * math.sin(t / 18.0)
        for s in range(symbols):
            if mode == "broad_up":
                slope = 0.12 if s < int(symbols * 0.80) else -0.025
            elif mode == "broad_down":
                slope = -0.11 if s < int(symbols * 0.80) else 0.02
            elif mode == "narrow_rally":
                slope = 0.15 if s < int(symbols * 0.25) else -0.015
            elif mode == "rotation":
                slope = 0.08 if (s + t // 20) % 3 == 0 else -0.025 if (s + t // 20) % 3 == 1 else 0.015
            elif mode == "divergence":
                slope = 0.10 if s < max(2, symbols - t // 18) else -0.08
            elif mode == "flat":
                slope = 0.0
            elif mode == "low_coverage":
                slope = 0.08 if s % 2 == 0 else -0.04
            else:
                slope = 0.05 if s % 2 == 0 else -0.02
            close = 80.0 + s * 1.7 + slope * t + 0.5 * math.sin(t / 7.0 + s)
            if mode == "flat":
                close = 100.0 + s * 0.0
            if mode == "low_coverage" and t > n - 8 and s >= 4:
                close = None
            volume = 1000.0 + t * 4.0 + s * 25.0
            rows.append(
                {
                    "ts": ts,
                    "symbol": f"S{s:02d}",
                    "close": close,
                    "volume": volume,
                    "weight": 1.0 + s / 50.0,
                    "index_close": index_close,
                }
            )
    return rows


def _wide_matrix():
    rows = _breadth_rows("rotation", n=160, symbols=14)
    frame = pd.DataFrame(rows).pivot_table(index="ts", columns="symbol", values="close", aggfunc="last").reset_index()
    return frame


def _aggregate_rows(n=160):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        advances = 12 + int(3 * math.sin(t / 8.0))
        declines = 5 + int(2 * math.cos(t / 9.0))
        unchanged = 2
        rows.append(
            {
                "ts": (start + timedelta(days=t)).isoformat().replace("+00:00", "Z"),
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "up_volume": advances * (1200.0 + t),
                "down_volume": declines * (900.0 + t),
                "new_highs": max(0, advances - 8),
                "new_lows": max(1, declines - 3),
                "index_close": 100.0 + t * 0.05,
            }
        )
    return rows


def test_all_breadth_modules_accept_long_records_and_dataframe():
    rows = _breadth_rows("broad_up")
    frame = pd.DataFrame(rows)
    for module_name in BREADTH_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls(min_symbols=8, min_coverage=0.5, high_low_window=60)))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.breadth_direction in {"bullish", "bearish", "neutral", "unknown"}, module_name
            assert result.value.breadth_state not in {"unknown"}, module_name
            assert result.value.sample_count is not None, module_name
            assert result.value.coverage is not None, module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_breadth_modules_handle_multiple_panel_regimes():
    for mode in ("broad_up", "broad_down", "narrow_rally", "rotation", "divergence"):
        rows = _breadth_rows(mode)
        for module_name in BREADTH_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls(min_symbols=8, min_coverage=0.5, high_low_window=60)))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] >= 60, module_name


def test_wide_matrix_supported_for_applicable_breadth_modules():
    frame = _wide_matrix()
    skipped = VOLUME_BREADTH | INDEX_BREADTH | {"cap_weighted_breadth"}
    for module_name in BREADTH_MODULES:
        if module_name in skipped:
            continue
        mod, params_cls, request_cls = _module_classes(module_name)
        result = mod.run(request_cls(data=frame, params=params_cls(min_symbols=8, min_coverage=0.5, high_low_window=60)))
        assert result.ok, (module_name, result.failure)
        assert result.value.summary["input_kind"] == "wide", module_name


def test_aggregate_rows_supported_for_applicable_breadth_modules():
    rows = _aggregate_rows()
    skipped = PANEL_ONLY
    for module_name in BREADTH_MODULES:
        if module_name in skipped:
            continue
        mod, params_cls, request_cls = _module_classes(module_name)
        result = mod.run(request_cls(data=rows, params=params_cls(min_symbols=8, min_coverage=0.5, high_low_window=60)))
        assert result.ok, (module_name, result.failure)
        assert result.value.summary["input_kind"] == "aggregate", module_name


def test_full_detail_returns_named_breadth_series():
    rows = _breadth_rows("rotation")
    for module_name in ("advance_decline_percent", "percent_above_ma", "breadth_regime", "breadth_freeze_pressure"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(min_symbols=8, min_coverage=0.5, high_low_window=60), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_breadth_respects_dataframe_spec_field_mapping():
    from quant_strategy_tokenizer.indicators.advance_decline_percent import AdvanceDeclinePercentParams, AdvanceDeclinePercentRequest, run as run_adp

    rows = []
    for row in _breadth_rows("broad_up", n=90, symbols=12):
        rows.append({"T": row["ts"], "symbol": row["symbol"], "C": row["close"], "V": row["volume"]})
    spec = DataFrameSpec(ts_col="T", close_col="C", volume_col="V")
    result = run_adp(AdvanceDeclinePercentRequest(data=rows, params=AdvanceDeclinePercentParams(min_symbols=8, min_coverage=0.5), spec=spec))
    assert result.ok, result.failure
    assert result.value.used_fields["ts"] == "T"
    assert result.value.used_fields["value"] == "C"
    assert result.value.used_fields["volume"] == "V"


def test_invalid_missing_sample_coverage_flat_and_volume_paths_fail():
    from quant_strategy_tokenizer.indicators.advance_decline_percent import AdvanceDeclinePercentParams, AdvanceDeclinePercentRequest, run as run_adp
    from quant_strategy_tokenizer.indicators.cap_weighted_breadth import CapWeightedBreadthRequest, run as run_cap
    from quant_strategy_tokenizer.indicators.mcclellan_oscillator import McClellanOscillatorParams, McClellanOscillatorRequest, run as run_mcclellan
    from quant_strategy_tokenizer.indicators.up_down_volume_ratio import UpDownVolumeRatioParams, UpDownVolumeRatioRequest, run as run_udv

    invalid_param = run_adp(AdvanceDeclinePercentRequest(data=_breadth_rows(), params=AdvanceDeclinePercentParams(window=0)))
    assert not invalid_param.ok
    assert invalid_param.failure.kind == "invalid_parameter"

    missing_symbol = run_adp(AdvanceDeclinePercentRequest(data=[{"ts": "2025-01-01T00:00:00Z", "close": 100.0}, {"ts": "2025-01-02T00:00:00Z", "close": 101.0}]))
    assert not missing_symbol.ok
    assert missing_symbol.failure.kind == "missing_required_field"

    missing_ts = run_adp(AdvanceDeclinePercentRequest(data=[{"symbol": "A", "close": 100.0}, {"symbol": "A", "close": 101.0}]))
    assert not missing_ts.ok
    assert missing_ts.failure.kind == "missing_required_field"

    missing_close = run_adp(AdvanceDeclinePercentRequest(data=[{"ts": "2025-01-01T00:00:00Z", "symbol": "A"}]))
    assert not missing_close.ok
    assert missing_close.failure.kind == "missing_required_field"

    missing_aggregate_counts = run_adp(AdvanceDeclinePercentRequest(data=[{"ts": "2025-01-01T00:00:00Z", "index_close": 100.0}]))
    assert not missing_aggregate_counts.ok

    short = run_mcclellan(McClellanOscillatorRequest(data=_breadth_rows(n=50), params=McClellanOscillatorParams(slow_window=80, min_symbols=8, min_coverage=0.5)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    insufficient_sample = run_adp(AdvanceDeclinePercentRequest(data=_breadth_rows(symbols=5), params=AdvanceDeclinePercentParams(min_symbols=8, min_coverage=0.5)))
    assert not insufficient_sample.ok
    assert insufficient_sample.failure.kind == "insufficient_sample"

    low_coverage = run_adp(AdvanceDeclinePercentRequest(data=_breadth_rows("low_coverage"), params=AdvanceDeclinePercentParams(min_symbols=3, min_coverage=0.8)))
    assert not low_coverage.ok
    assert low_coverage.failure.kind == "insufficient_coverage"

    flat = run_adp(AdvanceDeclinePercentRequest(data=_breadth_rows("flat"), params=AdvanceDeclinePercentParams(min_symbols=8, min_coverage=0.5)))
    assert not flat.ok
    assert flat.failure.kind == "insufficient_data"

    no_volume = [{k: v for k, v in row.items() if k != "volume"} for row in _breadth_rows()]
    volume_fail = run_udv(UpDownVolumeRatioRequest(data=no_volume))
    assert not volume_fail.ok
    assert volume_fail.failure.kind == "missing_required_field"

    zero_volume = [dict(row, volume=0.0) for row in _breadth_rows()]
    zero_volume_fail = run_udv(UpDownVolumeRatioRequest(data=zero_volume, params=UpDownVolumeRatioParams()))
    assert not zero_volume_fail.ok
    assert zero_volume_fail.failure.kind == "missing_required_field"

    no_weight = [{k: v for k, v in row.items() if k != "weight"} for row in _breadth_rows()]
    cap_fail = run_cap(CapWeightedBreadthRequest(data=no_weight))
    assert not cap_fail.ok
    assert cap_fail.failure.kind == "missing_required_field"


def test_breadth_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.breadth_regime import BreadthRegimeParams, BreadthRegimeRequest, run as run_regime

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="breadth_regime", run_id="breadth-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_regime(BreadthRegimeRequest(data=_breadth_rows(), params=BreadthRegimeParams(min_symbols=8, min_coverage=0.5), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_breadth_tokens():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.advance_decline_percent import AdvanceDeclinePercentParams, AdvanceDeclinePercentRequest, run as run_adp
    from quant_strategy_tokenizer.indicators.breadth_regime import BreadthRegimeParams, BreadthRegimeRequest, run as run_regime
    from quant_strategy_tokenizer.indicators.index_breadth_divergence import IndexBreadthDivergenceParams, IndexBreadthDivergenceRequest, run as run_divergence
    from quant_strategy_tokenizer.indicators.percent_above_ma import PercentAboveMaParams, PercentAboveMaRequest, run as run_above_ma

    rows = _breadth_rows("divergence")
    steps = [
        PipelineStep(
            name="ad_percent",
            input_key="initial",
            output_key="ad_percent",
            take="last_value",
            fn=lambda data: run_adp(AdvanceDeclinePercentRequest(data=data, params=AdvanceDeclinePercentParams(min_symbols=8, min_coverage=0.5))),
        ),
        PipelineStep(
            name="above_ma",
            input_key="initial",
            output_key="above_ma",
            take="last_value",
            fn=lambda data: run_above_ma(PercentAboveMaRequest(data=data, params=PercentAboveMaParams(min_symbols=8, min_coverage=0.5))),
        ),
        PipelineStep(
            name="regime",
            input_key="initial",
            output_key="regime",
            take="regime",
            fn=lambda data: run_regime(BreadthRegimeRequest(data=data, params=BreadthRegimeParams(min_symbols=8, min_coverage=0.5))),
        ),
        PipelineStep(
            name="divergence",
            input_key="initial",
            output_key="divergence",
            take="breadth_state",
            fn=lambda data: run_divergence(IndexBreadthDivergenceRequest(data=data, params=IndexBreadthDivergenceParams(min_symbols=8, min_coverage=0.5))),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "ad_percent": state.get("ad_percent"),
                    "above_ma": state.get("above_ma"),
                    "regime": state.get("regime"),
                    "divergence": state.get("divergence"),
                }
            ),
        ),
    ]
    result = run_pipeline(rows, steps)
    assert result.ok, result.failure
    assert "ad_percent" in result.value.final_payload
    assert result.value.final_payload["divergence"] in {"bearish_divergence", "bullish_divergence", "neutral"}


if __name__ == "__main__":
    test_all_breadth_modules_accept_long_records_and_dataframe()
    test_breadth_modules_handle_multiple_panel_regimes()
    test_wide_matrix_supported_for_applicable_breadth_modules()
    test_aggregate_rows_supported_for_applicable_breadth_modules()
    test_full_detail_returns_named_breadth_series()
    test_breadth_respects_dataframe_spec_field_mapping()
    test_invalid_missing_sample_coverage_flat_and_volume_paths_fail()
    test_breadth_output_dir_writes_standard_reports()
    test_pipeline_composes_breadth_tokens()
    print("breadth_indicator_tests_ok")
