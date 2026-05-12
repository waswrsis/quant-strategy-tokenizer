from pathlib import Path
import importlib
import math
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


STRUCTURE_MODULES = [
    "swing_points",
    "fractal_pivots",
    "zigzag_structure",
    "higher_high_lower_low",
    "market_structure_shift",
    "break_of_structure",
    "change_of_character",
    "trendline_structure",
    "pivot_points",
    "rolling_support_resistance",
    "support_resistance_zones",
    "nearest_support_resistance",
    "level_touch_count",
    "breakout_detector",
    "retest_detector",
    "false_breakout_detector",
    "range_box",
    "consolidation_zone",
    "inside_bar",
    "outside_bar",
    "narrow_range",
    "wide_range",
    "range_position",
    "range_breakout_strength",
    "price_gap",
    "fair_value_gap",
    "liquidity_sweep",
    "equal_highs_lows",
    "order_block_proxy",
    "supply_demand_zone",
    "volume_profile",
    "market_profile",
    "point_of_control",
    "value_area",
    "profile_acceptance",
]


def _structure_rows(mode="range_bound", n=360):
    rows = []
    for i in range(n):
        if mode == "trending_up":
            base = 80.0 + i * 0.09 + 2.4 * math.sin(i / 9.0)
        elif mode == "trending_down":
            base = 140.0 - i * 0.08 + 2.2 * math.sin(i / 10.0)
        elif mode == "breakout":
            base = 100.0 + 2.5 * math.sin(i / 8.0)
            if i > n * 0.70:
                base += 0.18 * (i - n * 0.70) + 8.0
        elif mode == "false_breakout":
            base = 100.0 + 2.0 * math.sin(i / 7.0)
            if int(n * 0.62) < i < int(n * 0.68):
                base += 8.0
        elif mode == "gap":
            base = 100.0 + 1.5 * math.sin(i / 8.0) + (7.0 if i > n * 0.55 else 0.0)
        elif mode == "sweep":
            base = 100.0 + 2.0 * math.sin(i / 8.0)
        elif mode == "profile_heavy":
            base = 100.0 + 0.9 * math.sin(i / 5.0) + 3.0 * math.sin(i / 33.0)
        else:
            base = 100.0 + 3.0 * math.sin(i / 8.0) + 0.4 * math.sin(i / 2.0)
        close = base + 0.16 * math.sin(i / 3.0)
        open_ = close - 0.35 * math.sin(i / 5.0)
        spread = 0.9 + 0.22 * abs(math.sin(i / 6.0))
        high = max(open_, close) + spread
        low = min(open_, close) - spread
        if mode == "sweep" and i in {210, 260}:
            high += 5.0
            close -= 1.5
        if mode == "gap" and i == int(n * 0.55) + 1:
            open_ += 7.0
            close += 6.0
            high += 7.0
            low += 5.5
        volume = 1400.0 + i * 2.0 + 250.0 * abs(math.sin(i / 9.0))
        if mode == "profile_heavy" and 97.0 <= close <= 103.0:
            volume *= 2.2
        rows.append(
            {
                "ts": f"2025-05-{(i % 28) + 1:02d}T00:00:00Z",
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


def test_all_structure_modules_accept_records_and_dataframes():
    rows = _structure_rows("range_bound")
    frame = pd.DataFrame(rows)
    for module_name in STRUCTURE_MODULES:
        mod, params_cls, request_cls = _module_classes(module_name)
        for payload in (rows, frame):
            result = mod.run(request_cls(data=payload, params=params_cls()))
            assert result.ok, (module_name, result.failure)
            assert result.value.quality == "ok", module_name
            assert result.value.indicator == module_name, module_name
            assert result.value.last_value is not None, module_name
            assert result.value.structure_bias in {"bullish", "bearish", "range", "mixed", "unknown"}, module_name
            assert result.value.structure_state in {"breakout", "breakdown", "retest", "sweep", "consolidation", "expansion", "neutral", "unknown"}, module_name
            assert isinstance(result.value.levels, list), module_name
            assert isinstance(result.value.zones, list), module_name
            assert result.value.series is None, module_name
            assert result.value.series_by_name is None, module_name


def test_structure_modules_handle_multiple_regimes():
    for mode in ("trending_up", "trending_down", "range_bound", "breakout", "false_breakout", "gap", "sweep", "profile_heavy"):
        rows = _structure_rows(mode)
        for module_name in STRUCTURE_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] == len(rows), module_name


def test_full_detail_returns_named_structure_series():
    rows = _structure_rows("breakout")
    for module_name in ("swing_points", "support_resistance_zones", "breakout_detector", "value_area", "liquidity_sweep"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=rows, params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name


def test_invalid_missing_flat_and_profile_inputs_fail_explicitly():
    from quant_strategy_tokenizer.indicators.breakout_detector import BreakoutDetectorParams, BreakoutDetectorRequest, run as run_breakout
    from quant_strategy_tokenizer.indicators.point_of_control import PointOfControlParams, PointOfControlRequest, run as run_poc
    from quant_strategy_tokenizer.indicators.swing_points import SwingPointsRequest, run as run_swings
    from quant_strategy_tokenizer.indicators.volume_profile import VolumeProfileRequest, run as run_volume_profile

    invalid = run_breakout(BreakoutDetectorRequest(data=_structure_rows(), params=BreakoutDetectorParams(window=0)))
    assert not invalid.ok
    assert invalid.failure.kind == "invalid_parameter"

    missing_ohlc = run_swings(SwingPointsRequest(data=[{"close": 100.0}, {"close": 101.0}]))
    assert not missing_ohlc.ok
    assert missing_ohlc.failure.kind == "missing_required_field"

    missing_volume = run_volume_profile(VolumeProfileRequest(data=[{"high": 2.0, "low": 1.0, "close": 1.5} for _ in range(40)]))
    assert not missing_volume.ok
    assert missing_volume.failure.kind == "missing_required_field"

    short = run_breakout(BreakoutDetectorRequest(data=_structure_rows(n=5), params=BreakoutDetectorParams(window=20)))
    assert not short.ok
    assert short.failure.kind == "insufficient_data"

    flat = [{"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1000.0} for _ in range(80)]
    flat_result = run_breakout(BreakoutDetectorRequest(data=flat))
    assert not flat_result.ok
    assert flat_result.failure.kind == "insufficient_data"

    invalid_bins = run_poc(PointOfControlRequest(data=_structure_rows("profile_heavy"), params=PointOfControlParams(profile_bins=1)))
    assert not invalid_bins.ok
    assert invalid_bins.failure.kind == "invalid_parameter"


def test_profile_and_order_block_reports_mark_approximations():
    from quant_strategy_tokenizer.indicators.order_block_proxy import OrderBlockProxyRequest, run as run_order_block
    from quant_strategy_tokenizer.indicators.volume_profile import VolumeProfileRequest, run as run_volume_profile

    profile = run_volume_profile(VolumeProfileRequest(data=_structure_rows("profile_heavy")))
    assert profile.ok, profile.failure
    assert profile.value.diagnostics.get("approximation") is True
    assert "not tick-level" in profile.value.diagnostics.get("approximation_note", "")

    order_block = run_order_block(OrderBlockProxyRequest(data=_structure_rows("breakout")))
    assert order_block.ok, order_block.failure
    assert order_block.value.diagnostics.get("approximation") is True
    assert "not footprint" in order_block.value.diagnostics.get("approximation_note", "")


def test_structure_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.support_resistance_zones import (
        SupportResistanceZonesParams,
        SupportResistanceZonesRequest,
        run as run_zones,
    )

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="support_resistance_zones", run_id="structure-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_zones(SupportResistanceZonesRequest(data=_structure_rows(), params=SupportResistanceZonesParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_pipeline_composes_swing_zones_and_breakout_tokens():
    from quant_strategy_tokenizer.contracts import ModuleResult
    from quant_strategy_tokenizer.indicators.breakout_detector import BreakoutDetectorParams, BreakoutDetectorRequest, run as run_breakout
    from quant_strategy_tokenizer.indicators.support_resistance_zones import (
        SupportResistanceZonesParams,
        SupportResistanceZonesRequest,
        run as run_zones,
    )
    from quant_strategy_tokenizer.indicators.swing_points import SwingPointsParams, SwingPointsRequest, run as run_swings

    steps = [
        PipelineStep(
            name="swings",
            input_key="initial",
            output_key="swing_levels",
            take="levels",
            fn=lambda data: run_swings(SwingPointsRequest(data=data, params=SwingPointsParams())),
        ),
        PipelineStep(
            name="zones",
            input_key="initial",
            output_key="zone_count",
            take="zones",
            fn=lambda data: run_zones(SupportResistanceZonesRequest(data=data, params=SupportResistanceZonesParams())),
        ),
        PipelineStep(
            name="breakout",
            input_key="initial",
            output_key="breakout_state",
            take="structure_state",
            fn=lambda data: run_breakout(BreakoutDetectorRequest(data=data, params=BreakoutDetectorParams())),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "swing_levels": len(state.get("swing_levels")),
                    "zones": len(state.get("zone_count")),
                    "breakout_state": state.get("breakout_state"),
                }
            ),
        ),
    ]
    result = run_pipeline(_structure_rows("breakout"), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["swing_levels"] >= 0
    assert result.value.final_payload["zones"] >= 0
    assert result.value.final_payload["breakout_state"] in {"breakout", "breakdown", "neutral"}


if __name__ == "__main__":
    test_all_structure_modules_accept_records_and_dataframes()
    test_structure_modules_handle_multiple_regimes()
    test_full_detail_returns_named_structure_series()
    test_invalid_missing_flat_and_profile_inputs_fail_explicitly()
    test_profile_and_order_block_reports_mark_approximations()
    test_structure_output_dir_writes_standard_reports()
    test_pipeline_composes_swing_zones_and_breakout_tokens()
    print("structure_indicator_tests_ok")
