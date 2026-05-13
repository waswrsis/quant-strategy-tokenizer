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
from quant_strategy_tokenizer.indicators.sentiment_common import SENTIMENT_INDICATORS


SENTIMENT_MODULES = sorted(SENTIMENT_INDICATORS)


def _module_classes(module_name):
    mod = importlib.import_module(f"quant_strategy_tokenizer.indicators.{module_name}")
    params_cls = getattr(mod, mod.__all__[0])
    request_cls = getattr(mod, mod.__all__[1])
    return mod, params_cls, request_cls


def _sentiment_rows(mode="normal", n=160, *, multi_source=False):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for t in range(n):
        ts = (start + timedelta(days=t)).isoformat().replace("+00:00", "Z")
        sentiment = 20.0 * math.sin(t / 18.0) + t * 0.05
        fear_greed = 50.0 + 25.0 * math.sin(t / 20.0)
        fund_flow = 1000.0 * math.sin(t / 14.0) + t * 5.0
        if mode == "optimism":
            sentiment += 45.0
            fear_greed = 82.0 + 5.0 * math.sin(t / 9.0)
        elif mode == "pessimism":
            sentiment -= 45.0
            fear_greed = 18.0 + 5.0 * math.sin(t / 9.0)
        elif mode == "high_attention":
            sentiment += 20.0
        elif mode == "fear":
            fear_greed = 15.0 + 3.0 * math.sin(t / 7.0)
        elif mode == "greed":
            fear_greed = 85.0 + 3.0 * math.sin(t / 7.0)
        elif mode == "inflow":
            fund_flow = 2000.0 + t * 20.0
        elif mode == "outflow":
            fund_flow = -2000.0 - t * 20.0
        positive = 800.0 + t * 3.0 + 80.0 * math.sin(t / 9.0)
        negative = 500.0 + 50.0 * math.cos(t / 10.0)
        if sentiment < -10:
            negative += abs(sentiment) * 5.0
        else:
            positive += max(sentiment, 0.0) * 5.0
        neutral = 300.0 + 20.0 * math.sin(t / 7.0)
        social_volume = positive + negative + neutral + 400.0
        news_volume = 300.0 + t * 2.0
        if mode == "high_attention":
            social_volume *= 2.4
            news_volume *= 2.0
        short_interest = 8.0 + 1.5 * math.sin(t / 12.0)
        borrow_rate = 2.0 + 0.3 * math.cos(t / 10.0)
        if mode == "short_crowded":
            short_interest += t * 0.03
            borrow_rate += t * 0.01
        policy_uncertainty = 100.0 + 10.0 * math.sin(t / 17.0)
        if mode == "policy_stress":
            policy_uncertainty += t * 0.5
        base = {
            "ts": ts,
            "price": 100.0 + t * 0.3,
            "sentiment_score": sentiment,
            "positive_mentions": positive,
            "negative_mentions": negative,
            "neutral_mentions": neutral,
            "total_mentions": positive + negative + neutral,
            "social_volume": social_volume,
            "news_sentiment": sentiment * 0.7,
            "news_volume": news_volume,
            "search_interest": 50.0 + 10.0 * math.sin(t / 11.0) + t * 0.05,
            "fear_greed_index": fear_greed,
            "survey_bullish": 45.0 + 10.0 * math.sin(t / 13.0) + (12.0 if mode == "optimism" else 0.0),
            "survey_bearish": 30.0 + 8.0 * math.cos(t / 15.0) + (12.0 if mode == "pessimism" else 0.0),
            "survey_neutral": 25.0,
            "fund_flow": fund_flow,
            "etf_flow": 800.0 * math.sin(t / 16.0) + t * 3.0,
            "short_interest": short_interest,
            "borrow_rate": borrow_rate,
            "margin_long": 50000.0 + t * 120.0 + 1000.0 * math.sin(t / 9.0),
            "margin_short": 30000.0 + t * 60.0 + 800.0 * math.cos(t / 12.0),
            "analyst_upgrades": 5.0 + max(0.0, math.sin(t / 8.0)) * 3.0 + (3.0 if mode == "analyst_positive" else 0.0),
            "analyst_downgrades": 3.0 + max(0.0, math.cos(t / 9.0)) * 2.0,
            "rating_score": 3.2 + 0.2 * math.sin(t / 20.0),
            "insider_buy_value": 200000.0 + 20000.0 * math.sin(t / 11.0) + t * 1000.0,
            "insider_sell_value": 150000.0 + 15000.0 * math.cos(t / 10.0) + t * 500.0,
            "policy_uncertainty": policy_uncertainty,
            "risk_aversion_index": 50.0 + 8.0 * math.cos(t / 15.0),
            "volatility_index": 20.0 + 3.0 * math.cos(t / 10.0),
            "safe_haven_flow": 100.0 * math.cos(t / 14.0),
            "put_call_ratio": 0.8 + 0.1 * math.sin(t / 16.0),
            "option_skew": 5.0 + 0.8 * math.cos(t / 18.0),
            "asset": "SYN",
        }
        if mode == "flat_invalid":
            base.update(
                {
                    "sentiment_score": 0.0,
                    "positive_mentions": 0.0,
                    "negative_mentions": 0.0,
                    "total_mentions": 0.0,
                    "social_volume": 0.0,
                    "fear_greed_index": 50.0,
                }
            )
        if multi_source:
            for source, weight in (("social", 0.55), ("news", 0.30), ("survey", 0.15)):
                row = base.copy()
                row["source"] = source
                row["positive_mentions"] *= weight
                row["negative_mentions"] *= weight
                row["neutral_mentions"] *= weight
                row["total_mentions"] *= weight
                row["social_volume"] *= weight
                rows.append(row)
        else:
            rows.append(base)
    return rows


def test_all_sentiment_modules_accept_records_and_dataframe():
    rows = _sentiment_rows()
    frame = pd.DataFrame(rows)
    for module_name in SENTIMENT_MODULES:
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


def test_sentiment_modules_handle_multiple_regimes_and_multisource_rows():
    for mode in ("normal", "optimism", "pessimism", "high_attention", "fear", "greed", "inflow", "outflow", "short_crowded", "analyst_positive", "policy_stress"):
        rows = _sentiment_rows(mode)
        for module_name in SENTIMENT_MODULES:
            mod, params_cls, request_cls = _module_classes(module_name)
            result = mod.run(request_cls(data=rows, params=params_cls()))
            assert result.ok, (mode, module_name, result.failure)
            assert result.value.summary["rows"] >= 80, module_name
    multi = _sentiment_rows(multi_source=True)
    mod, params_cls, request_cls = _module_classes("sentiment_score")
    result = mod.run(request_cls(data=multi, params=params_cls()))
    assert result.ok, result.failure
    assert result.value.summary["input_kind"] == "multi_source"


def test_sentiment_respects_dataframe_spec_field_mapping():
    from quant_strategy_tokenizer.indicators.sentiment_score import SentimentScoreParams, SentimentScoreRequest, run as run_sentiment

    rows = []
    for row in _sentiment_rows(n=90):
        rows.append({"time": row["ts"], "px": row["price"], "score": row["sentiment_score"]})
    spec = DataFrameSpec(ts_col="time", price_col="px")
    result = run_sentiment(SentimentScoreRequest(data=rows, params=SentimentScoreParams(sentiment_score_field="score"), spec=spec))
    assert result.ok, result.failure
    assert result.value.used_fields["ts"] == "time"
    assert result.value.used_fields["price"] == "px"
    assert result.value.used_fields["sentiment_score"] == "score"


def test_full_detail_returns_named_sentiment_series_and_proxy_diagnostics():
    for module_name in ("sentiment_zscore", "hype_pressure_index", "contrarian_sentiment_signal", "consensus_crowding_index"):
        mod, params_cls, request_cls = _module_classes(module_name)
        ctx = ModuleRunContext(module=module_name, detail_level=DetailLevel.FULL)
        result = mod.run(request_cls(data=_sentiment_rows(), params=params_cls(), context=ctx))
        assert result.ok, (module_name, result.failure)
        assert result.value.series is not None, module_name
        assert result.value.series_by_name is not None, module_name
        assert "value" in result.value.series_by_name, module_name
        if module_name in {"hype_pressure_index", "contrarian_sentiment_signal", "consensus_crowding_index"}:
            assert result.value.diagnostics.get("proxy") is True, module_name


def test_sentiment_output_dir_writes_standard_reports():
    from quant_strategy_tokenizer.indicators.sentiment_regime import SentimentRegimeParams, SentimentRegimeRequest, run as run_regime

    with tempfile.TemporaryDirectory() as tmp:
        ctx = ModuleRunContext(module="sentiment_regime", run_id="sentiment-test", output_dir=tmp, detail_level=DetailLevel.FULL)
        result = run_regime(SentimentRegimeRequest(data=_sentiment_rows(), params=SentimentRegimeParams(), context=ctx))
        assert result.ok, result.failure
        assert result.files is not None
        assert Path(result.files.summary_json).exists()
        assert Path(result.files.events_jsonl).exists()
        assert Path(result.files.data_json).exists()


def test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail():
    from quant_strategy_tokenizer.indicators.bull_bear_ratio import BullBearRatioRequest, run as run_bbr
    from quant_strategy_tokenizer.indicators.fear_greed_zscore import FearGreedZScoreRequest, run as run_fg
    from quant_strategy_tokenizer.indicators.positive_negative_mention_ratio import PositiveNegativeMentionRatioRequest, run as run_pn
    from quant_strategy_tokenizer.indicators.sentiment_score import SentimentScoreParams, SentimentScoreRequest, run as run_sentiment

    invalid_param = run_sentiment(SentimentScoreRequest(data=_sentiment_rows(), params=SentimentScoreParams(window=0)))
    assert not invalid_param.ok
    assert invalid_param.failure.kind == "invalid_parameter"

    missing_sentiment = run_sentiment(SentimentScoreRequest(data=[{"ts": "2025-01-01T00:00:00Z", "price": 100.0}]))
    assert not missing_sentiment.ok
    assert missing_sentiment.failure.kind == "missing_required_field"

    missing_survey = run_bbr(BullBearRatioRequest(data=[{"ts": "2025-01-01T00:00:00Z", "survey_bullish": 50.0}]))
    assert not missing_survey.ok
    assert missing_survey.failure.kind == "missing_required_field"

    short_window = run_fg(FearGreedZScoreRequest(data=_sentiment_rows(n=5)))
    assert not short_window.ok
    assert short_window.failure.kind == "insufficient_data"

    zero_mentions = [{**row, "negative_mentions": 0.0} for row in _sentiment_rows()]
    pn_res = run_pn(PositiveNegativeMentionRatioRequest(data=zero_mentions))
    assert not pn_res.ok
    assert pn_res.failure.kind == "insufficient_data"


def test_pipeline_composes_sentiment_tokens():
    from quant_strategy_tokenizer.indicators.attention_adjusted_sentiment import AttentionAdjustedSentimentRequest, run as run_adjusted
    from quant_strategy_tokenizer.indicators.fear_greed_zscore import FearGreedZScoreRequest, run as run_fg
    from quant_strategy_tokenizer.indicators.fund_flow_zscore import FundFlowZScoreRequest, run as run_flow
    from quant_strategy_tokenizer.indicators.sentiment_regime import SentimentRegimeRequest, run as run_regime

    rows = _sentiment_rows("optimism")
    result = run_pipeline(
        rows,
        [
            PipelineStep("fear_greed", lambda data: run_fg(FearGreedZScoreRequest(data=data)), input_key="initial", take="last_value", output_key="fear_greed_z"),
            PipelineStep("flow", lambda data: run_flow(FundFlowZScoreRequest(data=data)), input_key="initial", take="last_value", output_key="fund_flow_z"),
            PipelineStep("adjusted", lambda data: run_adjusted(AttentionAdjustedSentimentRequest(data=data)), input_key="initial", take="last_value", output_key="attention_adjusted"),
            PipelineStep("regime", lambda data: run_regime(SentimentRegimeRequest(data=data)), input_key="initial", take="sentiment_state", output_key="sentiment_state"),
        ],
    )
    assert result.ok, result.failure
    assert {"fear_greed_z", "fund_flow_z", "attention_adjusted", "sentiment_state"}.issubset(result.value.values)


if __name__ == "__main__":
    test_all_sentiment_modules_accept_records_and_dataframe()
    test_sentiment_modules_handle_multiple_regimes_and_multisource_rows()
    test_sentiment_respects_dataframe_spec_field_mapping()
    test_full_detail_returns_named_sentiment_series_and_proxy_diagnostics()
    test_sentiment_output_dir_writes_standard_reports()
    test_missing_fields_invalid_params_short_windows_and_zero_denominators_fail()
    test_pipeline_composes_sentiment_tokens()
    print("sentiment_indicator_tests_ok")
