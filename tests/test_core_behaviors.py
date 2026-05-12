from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.indicators.ema import EMAParams, EMARequest, run as run_ema
from quant_strategy_tokenizer.indicators.vwap import VWAPParams, VWAPRequest, run as run_vwap
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline


def _bars():
    closes = [100, 99, 98, 101, 103, 97, 96, 102, 104, 98, 105, 99]
    return [
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 100 + idx,
        }
        for idx, close in enumerate(closes)
    ]


def test_pipeline_composes_named_outputs_and_state():
    steps = [
        PipelineStep(
            name="vwap",
            input_key="initial",
            output_key="vwap_deviation",
            take="last_deviation",
            fn=lambda data: run_vwap(VWAPRequest(data=data, params=VWAPParams(window=3))),
        ),
        PipelineStep(
            name="ema",
            input_key="initial",
            output_key="ema_last",
            take="last_value",
            fn=lambda data: run_ema(EMARequest(data=data, params=EMAParams(window=3, min_periods=3))),
        ),
        PipelineStep(
            name="summary",
            pass_state=True,
            fn=lambda state: ModuleResult.success(
                {
                    "ema": state.get("ema_last"),
                    "vwap_deviation": state.get("vwap_deviation"),
                    "vwap_touches": state.get("vwap.touch_count"),
                }
            ),
        ),
    ]
    result = run_pipeline(_bars(), steps)
    assert result.ok, result.failure
    assert result.value.final_payload["ema"] is not None
    assert result.value.final_payload["vwap_deviation"] is not None
    assert result.value.final_payload["vwap_touches"] > 0


def test_vwap_default_touch_counts_crossovers():
    result = run_vwap(VWAPRequest(data=_bars(), params=VWAPParams(window=3)))
    assert result.ok, result.failure
    assert result.value.summary["touch_mode"] == "cross"
    assert result.value.cross_count > 0
    assert result.value.touch_count == result.value.cross_count


if __name__ == "__main__":
    test_pipeline_composes_named_outputs_and_state()
    test_vwap_default_touch_counts_crossovers()
    print("core_behavior_tests_ok")
