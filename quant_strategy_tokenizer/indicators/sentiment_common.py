"""
quant_strategy_tokenizer.indicators.sentiment_common
====================================================
Purpose: shared implementation layer for atomic market-sentiment indicator tokens.
Core idea: Normalize caller-supplied survey, social, news, search, flow,
positioning, analyst, insider, policy, and risk-appetite rows, then compute
explicit sentiment, attention, crowding, fear/greed, and contrarian diagnostics.
Assumes sentiment feeds are external inputs with vendor-specific meaning and
must not be fetched or inferred silently by this package.
Inputs: raw user data, optional DataFrameSpec/ExtractorSpec, SentimentParams,
indicator name, and ModuleRunContext.
Outputs: SentimentReport wrapped in ModuleResult with latest values, sentiment
direction/state, attention, crowding, fear/greed, flow, contrarian, and risk
states, optional series, diagnostics, warnings, and report files when requested.
Failure semantics: invalid params, missing fields, unsupported input shapes,
insufficient history, zero denominators, and calculation errors return
ModuleResult.fail.
Market generalization: calculations operate on caller-mapped numeric fields and
do not assume asset class, venue, sentiment vendor, social network, news source,
account access, or trade execution capability.
"""
from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..contracts import DataFrameSpec, DetailLevel, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext, detail_at_least
from ..reporting import write_module_report


@dataclass
class SentimentParams:
    """Generic sentiment-indicator options used by atomic wrapper modules.

    Configuration:
    - field names map caller data into survey, social, news, search, flow,
      crowding, analyst, insider, policy, and risk-appetite fields.
    - window fields are rows/bars on the input time axis.
    - thresholds label attention, crowding, fear/greed, and extreme z-score
      states; they do not trigger trades.
    """

    ts_field: str = "ts"
    price_field: str = "price"
    sentiment_score_field: str = "sentiment_score"
    positive_mentions_field: str = "positive_mentions"
    negative_mentions_field: str = "negative_mentions"
    neutral_mentions_field: str = "neutral_mentions"
    total_mentions_field: str = "total_mentions"
    social_volume_field: str = "social_volume"
    news_sentiment_field: str = "news_sentiment"
    news_volume_field: str = "news_volume"
    search_interest_field: str = "search_interest"
    fear_greed_index_field: str = "fear_greed_index"
    survey_bullish_field: str = "survey_bullish"
    survey_bearish_field: str = "survey_bearish"
    survey_neutral_field: str = "survey_neutral"
    fund_flow_field: str = "fund_flow"
    etf_flow_field: str = "etf_flow"
    short_interest_field: str = "short_interest"
    borrow_rate_field: str = "borrow_rate"
    margin_long_field: str = "margin_long"
    margin_short_field: str = "margin_short"
    analyst_upgrades_field: str = "analyst_upgrades"
    analyst_downgrades_field: str = "analyst_downgrades"
    rating_score_field: str = "rating_score"
    insider_buy_value_field: str = "insider_buy_value"
    insider_sell_value_field: str = "insider_sell_value"
    policy_uncertainty_field: str = "policy_uncertainty"
    risk_aversion_index_field: str = "risk_aversion_index"
    volatility_index_field: str = "volatility_index"
    safe_haven_flow_field: str = "safe_haven_flow"
    put_call_ratio_field: str = "put_call_ratio"
    option_skew_field: str = "option_skew"
    source_field: str = "source"
    asset_field: str = "asset"
    window: int = 20
    fast_window: int = 5
    slow_window: int = 30
    regime_window: int = 100
    high_percentile: float = 80.0
    low_percentile: float = 20.0
    extreme_zscore: float = 2.0
    crowding_threshold: float = 70.0
    fear_threshold: float = 25.0
    greed_threshold: float = 75.0


@dataclass
class SentimentReport:
    quality: str
    indicator: str
    last_value: Optional[float]
    last_values: Dict[str, Optional[float]] = field(default_factory=dict)
    sentiment_direction: str = "unknown"
    sentiment_state: str = "unknown"
    attention_state: str = "unknown"
    crowding_state: str = "unknown"
    fear_greed_state: str = "unknown"
    flow_state: str = "unknown"
    contrarian_state: str = "unknown"
    risk_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    series: Optional[List[Optional[float]]] = None
    series_by_name: Optional[Dict[str, List[Optional[float]]]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    used_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _SentimentData:
    kind: str
    frame: pd.DataFrame
    used_fields: Dict[str, str] = field(default_factory=dict)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class _ComputeOutput:
    primary: pd.Series
    series: Dict[str, pd.Series]
    sentiment_direction: str = "unknown"
    sentiment_state: str = "unknown"
    attention_state: str = "unknown"
    crowding_state: str = "unknown"
    fear_greed_state: str = "unknown"
    flow_state: str = "unknown"
    contrarian_state: str = "unknown"
    risk_state: str = "unknown"
    signal: str = "none"
    regime: str = "unknown"
    normalized_value: Optional[float] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


SENTIMENT_INDICATORS = {
    "sentiment_score",
    "sentiment_zscore",
    "sentiment_momentum",
    "bullish_percent",
    "bearish_percent",
    "bull_bear_spread",
    "bull_bear_ratio",
    "survey_sentiment_index",
    "social_volume",
    "social_sentiment_score",
    "social_sentiment_zscore",
    "news_sentiment_score",
    "news_sentiment_zscore",
    "positive_negative_mention_ratio",
    "mention_volume_zscore",
    "search_interest_zscore",
    "attention_momentum",
    "hype_pressure_index",
    "fear_greed_index",
    "fear_greed_zscore",
    "risk_appetite_index",
    "risk_aversion_zscore",
    "volatility_fear_proxy",
    "safe_haven_flow_pressure",
    "fund_flow",
    "fund_flow_zscore",
    "etf_flow_zscore",
    "short_interest_ratio",
    "short_interest_zscore",
    "borrow_rate_pressure",
    "margin_long_short_ratio",
    "margin_crowding_score",
    "put_call_sentiment",
    "option_skew_sentiment",
    "analyst_revision_balance",
    "analyst_upgrade_downgrade_ratio",
    "rating_score",
    "insider_buy_sell_ratio",
    "insider_flow_pressure",
    "policy_uncertainty_zscore",
    "sentiment_regime",
    "sentiment_extreme_index",
    "contrarian_sentiment_signal",
    "consensus_crowding_index",
    "attention_adjusted_sentiment",
    "sentiment_flow_confirmation",
}


PROXY_INDICATORS = {
    "volatility_fear_proxy",
    "hype_pressure_index",
    "contrarian_sentiment_signal",
    "consensus_crowding_index",
}


def normalize_sentiment_input(request: Any) -> ModuleResult[_SentimentData]:
    params = request.params
    spec = request.spec or DataFrameSpec()
    raw = _raw_to_frame(request.data, request.extractor)
    if not raw.ok:
        return raw
    frame = raw.value
    if frame is None or frame.empty:
        return ModuleResult.fail("empty_input", "sentiment input contains no rows")
    frame = frame.copy()
    cols = {str(c): c for c in frame.columns}
    used: Dict[str, str] = {}
    field_candidates = {
        "ts": [params.ts_field, spec.ts_col],
        "price": [params.price_field, spec.price_col, spec.value_col, spec.close_col],
        "sentiment_score": [params.sentiment_score_field],
        "positive_mentions": [params.positive_mentions_field],
        "negative_mentions": [params.negative_mentions_field],
        "neutral_mentions": [params.neutral_mentions_field],
        "total_mentions": [params.total_mentions_field],
        "social_volume": [params.social_volume_field],
        "news_sentiment": [params.news_sentiment_field],
        "news_volume": [params.news_volume_field],
        "search_interest": [params.search_interest_field],
        "fear_greed_index": [params.fear_greed_index_field],
        "survey_bullish": [params.survey_bullish_field],
        "survey_bearish": [params.survey_bearish_field],
        "survey_neutral": [params.survey_neutral_field],
        "fund_flow": [params.fund_flow_field],
        "etf_flow": [params.etf_flow_field],
        "short_interest": [params.short_interest_field],
        "borrow_rate": [params.borrow_rate_field],
        "margin_long": [params.margin_long_field],
        "margin_short": [params.margin_short_field],
        "analyst_upgrades": [params.analyst_upgrades_field],
        "analyst_downgrades": [params.analyst_downgrades_field],
        "rating_score": [params.rating_score_field],
        "insider_buy_value": [params.insider_buy_value_field],
        "insider_sell_value": [params.insider_sell_value_field],
        "policy_uncertainty": [params.policy_uncertainty_field],
        "risk_aversion_index": [params.risk_aversion_index_field],
        "volatility_index": [params.volatility_index_field],
        "safe_haven_flow": [params.safe_haven_flow_field],
        "put_call_ratio": [params.put_call_ratio_field],
        "option_skew": [params.option_skew_field],
        "source": [params.source_field],
        "asset": [params.asset_field],
    }
    for logical, names in field_candidates.items():
        col = _find_any_col(cols, names)
        if col is not None:
            used[logical] = str(col)

    if "ts" in used:
        converted = pd.to_datetime(frame[used["ts"]], utc=True, errors="coerce")
        if converted.isna().any():
            return ModuleResult.fail("invalid_timestamp", "timestamp field contains invalid values", field=used["ts"])
        frame["__ts"] = converted
    else:
        frame["__ts"] = pd.RangeIndex(len(frame))

    for logical, col in used.items():
        if logical in {"ts", "source", "asset"}:
            continue
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    kind = "multi_source" if "source" in used else "aggregate"
    frame = frame.sort_values("__ts").reset_index(drop=True)
    profile = {
        "input_type": type(request.data).__name__,
        "rows": int(len(frame)),
        "columns": [str(c) for c in frame.columns if not str(c).startswith("__")],
    }
    return ModuleResult.success(_SentimentData(kind=kind, frame=frame, used_fields=used, input_profile=profile, warnings=list(raw.warnings)))


def run_sentiment_indicator(indicator: str, request: Any, *, module_name: str) -> ModuleResult[SentimentReport]:
    params = request.params
    param_error = _validate_params(params)
    if param_error is not None:
        return param_error
    norm = normalize_sentiment_input(request)
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    data = norm.value
    if data is None:
        return ModuleResult.fail("internal_error", "sentiment normalization returned no data")
    missing = _missing_required_fields(indicator, data)
    if missing:
        return ModuleResult.fail("missing_required_field", f"{indicator} requires fields: {missing}", details={"missing_fields": missing})
    min_rows = _minimum_rows(indicator, params)
    row_count = _time_row_count(data)
    if row_count < min_rows:
        return ModuleResult.fail("insufficient_data", f"need at least {min_rows} time rows, got {row_count}")
    try:
        computed = _compute_indicator(indicator, params, data)
    except ValueError as exc:
        message = str(exc)
        if "no usable numeric values" in message:
            return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output", details={"error": message})
        return ModuleResult.fail("calculation_error", f"{indicator} calculation failed", details={"error": message, "error_type": type(exc).__name__})
    except Exception as exc:
        return ModuleResult.fail("calculation_error", f"{indicator} calculation failed", details={"error": str(exc), "error_type": type(exc).__name__})

    primary = computed.primary.replace([np.inf, -np.inf], np.nan)
    last = _last_float(primary)
    if last is None:
        return ModuleResult.fail("insufficient_data", f"{indicator} produced no valid output")
    series_map = {name: ser.replace([np.inf, -np.inf], np.nan) for name, ser in computed.series.items()}
    if "value" not in series_map:
        series_map["value"] = primary
    last_values = {name: _last_float(ser) for name, ser in series_map.items()}
    include_series = detail_at_least(request.context.detail_level, DetailLevel.FULL)
    diagnostics = {"module": module_name, "indicator": indicator, **computed.diagnostics}
    if indicator in PROXY_INDICATORS:
        diagnostics["proxy"] = True
        diagnostics["proxy_note"] = f"{indicator} is a caller-data proxy, not observed investor intent or a fetched sentiment feed."
    report = SentimentReport(
        quality="ok",
        indicator=indicator,
        last_value=last,
        last_values=last_values,
        sentiment_direction=computed.sentiment_direction,
        sentiment_state=computed.sentiment_state,
        attention_state=computed.attention_state,
        crowding_state=computed.crowding_state,
        fear_greed_state=computed.fear_greed_state,
        flow_state=computed.flow_state,
        contrarian_state=computed.contrarian_state,
        risk_state=computed.risk_state,
        signal=computed.signal,
        regime=computed.regime,
        normalized_value=computed.normalized_value,
        series=_series_to_json(primary) if include_series else None,
        series_by_name={name: _series_to_json(ser) for name, ser in series_map.items()} if include_series else None,
        summary={"rows": row_count, "input_kind": data.kind, **computed.summary},
        input_profile=data.input_profile,
        used_fields=data.used_fields,
        warnings=data.warnings,
        diagnostics=diagnostics,
    )
    result = ModuleResult.success(
        report,
        events=[ModuleEvent(event=f"{indicator}.calculated", fields={"last_value": last, "risk_state": report.risk_state, "sentiment_state": report.sentiment_state})],
        warnings=data.warnings,
    )
    if request.context.output_dir:
        result.files = write_module_report(module_name, result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _compute_indicator(indicator: str, p: SentimentParams, data: _SentimentData) -> _ComputeOutput:
    sentiment = _sentiment_score(data)
    pos = _optional_series(data, "positive_mentions")
    neg = _optional_series(data, "negative_mentions")
    total_mentions = _total_mentions(data)
    social_volume = _optional_series(data, "social_volume")
    news_sentiment = _optional_series(data, "news_sentiment")
    news_volume = _optional_series(data, "news_volume")
    search = _optional_series(data, "search_interest")
    fear_greed = _optional_series(data, "fear_greed_index")
    bull = _optional_series(data, "survey_bullish")
    bear = _optional_series(data, "survey_bearish")
    fund_flow = _optional_series(data, "fund_flow")
    etf_flow = _optional_series(data, "etf_flow")
    short_interest = _optional_series(data, "short_interest")
    borrow_rate = _optional_series(data, "borrow_rate")
    margin_long = _optional_series(data, "margin_long")
    margin_short = _optional_series(data, "margin_short")
    upgrades = _optional_series(data, "analyst_upgrades")
    downgrades = _optional_series(data, "analyst_downgrades")
    rating = _optional_series(data, "rating_score")
    insider_buy = _optional_series(data, "insider_buy_value")
    insider_sell = _optional_series(data, "insider_sell_value")
    policy = _optional_series(data, "policy_uncertainty")
    risk_aversion = _optional_series(data, "risk_aversion_index")
    vol_index = _optional_series(data, "volatility_index")
    safe_haven = _optional_series(data, "safe_haven_flow")
    put_call = _optional_series(data, "put_call_ratio")
    option_skew = _optional_series(data, "option_skew")
    attention = _attention_index(total_mentions, social_volume, news_volume, search, p)
    flow = _flow_index(fund_flow, etf_flow, p)
    crowding = _crowding_index(sentiment, fear_greed, short_interest, borrow_rate, put_call, option_skew, p)

    if indicator == "sentiment_score":
        primary = _require_series(sentiment, "sentiment_score")
    elif indicator == "sentiment_zscore":
        primary = _zscore(_require_series(sentiment, "sentiment_score"), int(p.window))
    elif indicator == "sentiment_momentum":
        primary = _require_series(sentiment, "sentiment_score").diff(int(p.fast_window))
    elif indicator == "bullish_percent":
        primary = _require_series(bull, "survey_bullish")
    elif indicator == "bearish_percent":
        primary = _require_series(bear, "survey_bearish")
    elif indicator == "bull_bear_spread":
        primary = _require_series(bull, "survey_bullish") - _require_series(bear, "survey_bearish")
    elif indicator == "bull_bear_ratio":
        primary = _require_series(bull, "survey_bullish") / _require_series(bear, "survey_bearish").replace(0, np.nan)
    elif indicator == "survey_sentiment_index":
        primary = (_require_series(bull, "survey_bullish") - _require_series(bear, "survey_bearish")) / (_require_series(bull, "survey_bullish") + _require_series(bear, "survey_bearish")).replace(0, np.nan) * 100.0
    elif indicator == "social_volume":
        primary = _require_series(social_volume, "social_volume")
    elif indicator == "social_sentiment_score":
        primary = _mention_sentiment(data)
    elif indicator == "social_sentiment_zscore":
        primary = _zscore(_mention_sentiment(data), int(p.window))
    elif indicator == "news_sentiment_score":
        primary = _require_series(news_sentiment, "news_sentiment")
    elif indicator == "news_sentiment_zscore":
        primary = _zscore(_require_series(news_sentiment, "news_sentiment"), int(p.window))
    elif indicator == "positive_negative_mention_ratio":
        primary = _require_series(pos, "positive_mentions") / _require_series(neg, "negative_mentions").replace(0, np.nan)
    elif indicator == "mention_volume_zscore":
        primary = _zscore(_require_series(total_mentions, "total_mentions"), int(p.window))
    elif indicator == "search_interest_zscore":
        primary = _zscore(_require_series(search, "search_interest"), int(p.window))
    elif indicator == "attention_momentum":
        primary = _require_series(attention, "attention_index").diff(int(p.fast_window))
    elif indicator == "hype_pressure_index":
        primary = pd.concat([_safe_zscore(attention, p), _safe_zscore(sentiment, p)], axis=1).mean(axis=1)
    elif indicator == "fear_greed_index":
        primary = _require_series(fear_greed, "fear_greed_index")
    elif indicator == "fear_greed_zscore":
        primary = _zscore(_require_series(fear_greed, "fear_greed_index"), int(p.window))
    elif indicator == "risk_appetite_index":
        primary = _risk_appetite(fear_greed, risk_aversion, vol_index, safe_haven, p)
    elif indicator == "risk_aversion_zscore":
        primary = _zscore(_require_series(risk_aversion, "risk_aversion_index"), int(p.window))
    elif indicator == "volatility_fear_proxy":
        primary = _bounded_zscore(_require_series(vol_index, "volatility_index"), int(p.window))
    elif indicator == "safe_haven_flow_pressure":
        primary = _zscore(_require_series(safe_haven, "safe_haven_flow"), int(p.window))
    elif indicator == "fund_flow":
        primary = _require_series(fund_flow, "fund_flow")
    elif indicator == "fund_flow_zscore":
        primary = _zscore(_require_series(fund_flow, "fund_flow"), int(p.window))
    elif indicator == "etf_flow_zscore":
        primary = _zscore(_require_series(etf_flow, "etf_flow"), int(p.window))
    elif indicator == "short_interest_ratio":
        primary = _require_series(short_interest, "short_interest")
    elif indicator == "short_interest_zscore":
        primary = _zscore(_require_series(short_interest, "short_interest"), int(p.window))
    elif indicator == "borrow_rate_pressure":
        primary = _zscore(_require_series(borrow_rate, "borrow_rate"), int(p.window))
    elif indicator == "margin_long_short_ratio":
        primary = _require_series(margin_long, "margin_long") / _require_series(margin_short, "margin_short").replace(0, np.nan)
    elif indicator == "margin_crowding_score":
        ratio = _require_series(margin_long, "margin_long") / _require_series(margin_short, "margin_short").replace(0, np.nan)
        primary = _bounded_zscore(ratio, int(p.window))
    elif indicator == "put_call_sentiment":
        primary = -_zscore(_require_series(put_call, "put_call_ratio"), int(p.window))
    elif indicator == "option_skew_sentiment":
        primary = -_zscore(_require_series(option_skew, "option_skew"), int(p.window))
    elif indicator == "analyst_revision_balance":
        primary = _require_series(upgrades, "analyst_upgrades") - _require_series(downgrades, "analyst_downgrades")
    elif indicator == "analyst_upgrade_downgrade_ratio":
        primary = _require_series(upgrades, "analyst_upgrades") / _require_series(downgrades, "analyst_downgrades").replace(0, np.nan)
    elif indicator == "rating_score":
        primary = _require_series(rating, "rating_score")
    elif indicator == "insider_buy_sell_ratio":
        primary = _require_series(insider_buy, "insider_buy_value") / _require_series(insider_sell, "insider_sell_value").replace(0, np.nan)
    elif indicator == "insider_flow_pressure":
        primary = _zscore(_require_series(insider_buy, "insider_buy_value") - _require_series(insider_sell, "insider_sell_value"), int(p.window))
    elif indicator == "policy_uncertainty_zscore":
        primary = _zscore(_require_series(policy, "policy_uncertainty"), int(p.window))
    elif indicator == "sentiment_regime":
        primary = _composite([_safe_zscore(sentiment, p), _safe_zscore(fear_greed, p), _safe_zscore(flow, p)], invert=False)
    elif indicator == "sentiment_extreme_index":
        primary = _composite([_safe_zscore(sentiment, p).abs(), _safe_zscore(fear_greed, p).abs(), _safe_zscore(attention, p).abs()], invert=False)
    elif indicator == "contrarian_sentiment_signal":
        primary = -_composite([_safe_zscore(sentiment, p), _safe_zscore(fear_greed, p), _safe_zscore(attention, p)], invert=False)
    elif indicator == "consensus_crowding_index":
        primary = crowding
    elif indicator == "attention_adjusted_sentiment":
        primary = _require_series(sentiment, "sentiment_score") * (_bounded_zscore(_require_series(attention, "attention_index"), int(p.window)) / 100.0)
    elif indicator == "sentiment_flow_confirmation":
        primary = _require_series(sentiment, "sentiment_score") * np.sign(_require_series(flow, "flow_index"))
    else:
        raise ValueError(f"unsupported sentiment indicator {indicator}")

    normalized = _normalized(primary, p)
    last_sentiment = _last_float(sentiment)
    last_attention = _last_float(attention)
    last_crowding = _last_float(crowding)
    last_flow = _last_float(flow)
    last_fg = _last_float(fear_greed)
    sentiment_direction = _direction(last_sentiment)
    sentiment_state = _sentiment_state(last_sentiment)
    attention_state = _attention_state(last_attention, p)
    crowding_state = _crowding_state(last_crowding, p)
    fear_greed_state = _fear_greed_state(last_fg, p)
    flow_state = _flow_state(last_flow)
    contrarian_state = _contrarian_state(sentiment_state, attention_state, fear_greed_state)
    risk_state = _risk_state(normalized, p)
    series = {"value": primary}
    for name, ser in (
        ("sentiment_score", sentiment),
        ("total_mentions", total_mentions),
        ("attention_index", attention),
        ("fear_greed_index", fear_greed),
        ("fund_flow", fund_flow),
        ("etf_flow", etf_flow),
        ("crowding_index", crowding),
        ("flow_index", flow),
        ("news_sentiment", news_sentiment),
        ("social_volume", social_volume),
        ("search_interest", search),
    ):
        if ser is not None:
            series[name] = ser
    return _ComputeOutput(
        primary=primary,
        series=series,
        sentiment_direction=sentiment_direction,
        sentiment_state=sentiment_state,
        attention_state=attention_state,
        crowding_state=crowding_state,
        fear_greed_state=fear_greed_state,
        flow_state=flow_state,
        contrarian_state=contrarian_state,
        risk_state=risk_state,
        signal=_signal(sentiment_state, attention_state, crowding_state, fear_greed_state, flow_state),
        regime=risk_state,
        normalized_value=normalized,
        summary={"calculation": indicator},
    )


def _validate_params(p: SentimentParams) -> Optional[ModuleResult[Any]]:
    for name in ("window", "fast_window", "slow_window", "regime_window"):
        try:
            value = int(getattr(p, name))
        except Exception:
            return ModuleResult.fail("invalid_parameter", f"{name} must be an integer", field=name)
        if value <= 0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be positive", field=name)
    if int(p.fast_window) >= int(p.slow_window):
        return ModuleResult.fail("invalid_parameter", "fast_window must be smaller than slow_window", field="fast_window")
    for name in ("high_percentile", "low_percentile", "crowding_threshold", "fear_threshold", "greed_threshold"):
        value = _safe_float(getattr(p, name))
        if value is None or value < 0.0 or value > 100.0:
            return ModuleResult.fail("invalid_parameter", f"{name} must be between 0 and 100", field=name)
    if float(p.low_percentile) >= float(p.high_percentile):
        return ModuleResult.fail("invalid_parameter", "low_percentile must be below high_percentile", field="low_percentile")
    if float(p.fear_threshold) >= float(p.greed_threshold):
        return ModuleResult.fail("invalid_parameter", "fear_threshold must be below greed_threshold", field="fear_threshold")
    if _safe_float(p.extreme_zscore) is None or float(p.extreme_zscore) <= 0.0:
        return ModuleResult.fail("invalid_parameter", "extreme_zscore must be positive", field="extreme_zscore")
    return None


def _missing_required_fields(indicator: str, data: _SentimentData) -> List[str]:
    used = data.used_fields
    req: Dict[str, List[str]] = {
        "bullish_percent": ["survey_bullish"],
        "bearish_percent": ["survey_bearish"],
        "bull_bear_spread": ["survey_bullish", "survey_bearish"],
        "bull_bear_ratio": ["survey_bullish", "survey_bearish"],
        "survey_sentiment_index": ["survey_bullish", "survey_bearish"],
        "social_volume": ["social_volume"],
        "news_sentiment_score": ["news_sentiment"],
        "news_sentiment_zscore": ["news_sentiment"],
        "positive_negative_mention_ratio": ["positive_mentions", "negative_mentions"],
        "search_interest_zscore": ["search_interest"],
        "fear_greed_index": ["fear_greed_index"],
        "fear_greed_zscore": ["fear_greed_index"],
        "risk_aversion_zscore": ["risk_aversion_index"],
        "volatility_fear_proxy": ["volatility_index"],
        "safe_haven_flow_pressure": ["safe_haven_flow"],
        "fund_flow": ["fund_flow"],
        "fund_flow_zscore": ["fund_flow"],
        "etf_flow_zscore": ["etf_flow"],
        "short_interest_ratio": ["short_interest"],
        "short_interest_zscore": ["short_interest"],
        "borrow_rate_pressure": ["borrow_rate"],
        "margin_long_short_ratio": ["margin_long", "margin_short"],
        "margin_crowding_score": ["margin_long", "margin_short"],
        "put_call_sentiment": ["put_call_ratio"],
        "option_skew_sentiment": ["option_skew"],
        "analyst_revision_balance": ["analyst_upgrades", "analyst_downgrades"],
        "analyst_upgrade_downgrade_ratio": ["analyst_upgrades", "analyst_downgrades"],
        "rating_score": ["rating_score"],
        "insider_buy_sell_ratio": ["insider_buy_value", "insider_sell_value"],
        "insider_flow_pressure": ["insider_buy_value", "insider_sell_value"],
        "policy_uncertainty_zscore": ["policy_uncertainty"],
    }
    if indicator in {"sentiment_score", "sentiment_zscore", "sentiment_momentum", "attention_adjusted_sentiment", "sentiment_flow_confirmation"}:
        return [] if "sentiment_score" in used or ("positive_mentions" in used and "negative_mentions" in used) else ["sentiment_score or positive_mentions plus negative_mentions"]
    if indicator in {"social_sentiment_score", "social_sentiment_zscore"}:
        return [] if "sentiment_score" in used or ("positive_mentions" in used and "negative_mentions" in used) else ["sentiment_score or positive_mentions plus negative_mentions"]
    if indicator in {"mention_volume_zscore"}:
        return [] if any(name in used for name in ("total_mentions", "positive_mentions", "negative_mentions", "neutral_mentions", "social_volume")) else ["total_mentions or mention fields/social_volume"]
    if indicator in {"attention_momentum", "hype_pressure_index"}:
        return [] if any(name in used for name in ("total_mentions", "social_volume", "news_volume", "search_interest")) else ["one of total_mentions/social_volume/news_volume/search_interest"]
    if indicator == "risk_appetite_index":
        return [] if any(name in used for name in ("fear_greed_index", "risk_aversion_index", "volatility_index", "safe_haven_flow")) else ["one of fear_greed_index/risk_aversion_index/volatility_index/safe_haven_flow"]
    if indicator in {"sentiment_regime", "sentiment_extreme_index", "contrarian_sentiment_signal"}:
        return [] if ("sentiment_score" in used or ("positive_mentions" in used and "negative_mentions" in used)) and any(name in used for name in ("fear_greed_index", "total_mentions", "social_volume", "news_volume", "search_interest")) else ["sentiment plus fear_greed/attention fields"]
    if indicator == "consensus_crowding_index":
        return [] if any(name in used for name in ("sentiment_score", "fear_greed_index", "short_interest", "borrow_rate", "put_call_ratio", "option_skew")) else ["one crowding field"]
    required = req.get(indicator, [])
    return [name for name in required if name not in used]


def _minimum_rows(indicator: str, p: SentimentParams) -> int:
    if indicator.endswith("_zscore") or indicator in {"mention_volume_zscore", "search_interest_zscore", "margin_crowding_score", "put_call_sentiment", "option_skew_sentiment", "sentiment_regime", "sentiment_extreme_index", "contrarian_sentiment_signal", "consensus_crowding_index", "hype_pressure_index", "risk_appetite_index"}:
        return int(p.window)
    if indicator.endswith("_momentum"):
        return max(2, int(p.fast_window))
    return 1


def _time_row_count(data: _SentimentData) -> int:
    return int(data.frame["__ts"].nunique())


def _time_series(data: _SentimentData, logical: str, agg: str = "last") -> Optional[pd.Series]:
    col = data.used_fields.get(logical)
    if col is None:
        return None
    grouped = data.frame.groupby("__ts", sort=True)[col]
    if agg == "sum":
        out = grouped.sum(min_count=1)
    elif agg == "mean":
        out = grouped.mean()
    else:
        out = grouped.last()
    return pd.to_numeric(out, errors="coerce")


def _optional_series(data: _SentimentData, logical: str) -> Optional[pd.Series]:
    agg = "sum" if logical in {"positive_mentions", "negative_mentions", "neutral_mentions", "total_mentions", "social_volume", "news_volume", "fund_flow", "etf_flow", "analyst_upgrades", "analyst_downgrades", "insider_buy_value", "insider_sell_value"} else "last"
    return _time_series(data, logical, agg=agg)


def _require_series(series: Optional[pd.Series], name: str) -> pd.Series:
    if series is None or series.dropna().empty:
        raise ValueError(f"{name} has no usable numeric values")
    return series


def _sentiment_score(data: _SentimentData) -> Optional[pd.Series]:
    direct = _optional_series(data, "sentiment_score")
    if direct is not None and not direct.dropna().empty:
        return direct
    return _mention_sentiment(data)


def _mention_sentiment(data: _SentimentData) -> pd.Series:
    pos = _require_series(_optional_series(data, "positive_mentions"), "positive_mentions")
    neg = _require_series(_optional_series(data, "negative_mentions"), "negative_mentions")
    neutral = _optional_series(data, "neutral_mentions")
    denom = pos + neg + (neutral if neutral is not None else 0.0)
    return (pos - neg) / denom.replace(0, np.nan) * 100.0


def _total_mentions(data: _SentimentData) -> Optional[pd.Series]:
    direct = _optional_series(data, "total_mentions")
    if direct is not None and not direct.dropna().empty:
        return direct
    pieces = [_optional_series(data, "positive_mentions"), _optional_series(data, "negative_mentions"), _optional_series(data, "neutral_mentions")]
    usable = [ser for ser in pieces if ser is not None]
    if usable:
        return pd.concat(usable, axis=1).sum(axis=1, min_count=1)
    return _optional_series(data, "social_volume")


def _attention_index(total_mentions: Optional[pd.Series], social_volume: Optional[pd.Series], news_volume: Optional[pd.Series], search: Optional[pd.Series], p: SentimentParams) -> Optional[pd.Series]:
    parts = []
    for ser in (total_mentions, social_volume, news_volume, search):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(_bounded_zscore(ser, int(p.window)))
    if not parts:
        return None
    return pd.concat(parts, axis=1).mean(axis=1)


def _flow_index(fund_flow: Optional[pd.Series], etf_flow: Optional[pd.Series], p: SentimentParams) -> Optional[pd.Series]:
    parts = []
    for ser in (fund_flow, etf_flow):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(_zscore(ser, int(p.window)))
    if not parts:
        return None
    return pd.concat(parts, axis=1).mean(axis=1)


def _crowding_index(sentiment: Optional[pd.Series], fear_greed: Optional[pd.Series], short_interest: Optional[pd.Series], borrow_rate: Optional[pd.Series], put_call: Optional[pd.Series], option_skew: Optional[pd.Series], p: SentimentParams) -> Optional[pd.Series]:
    parts = []
    for ser in (sentiment, fear_greed, short_interest, borrow_rate, put_call, option_skew):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(_bounded_zscore(ser, int(p.window)))
    if not parts:
        return None
    return pd.concat(parts, axis=1).mean(axis=1)


def _risk_appetite(fear_greed: Optional[pd.Series], risk_aversion: Optional[pd.Series], vol_index: Optional[pd.Series], safe_haven: Optional[pd.Series], p: SentimentParams) -> pd.Series:
    parts = []
    if fear_greed is not None and len(fear_greed.dropna()) >= int(p.window):
        parts.append(_bounded_zscore(fear_greed, int(p.window)))
    for ser in (risk_aversion, vol_index, safe_haven):
        if ser is not None and len(ser.dropna()) >= int(p.window):
            parts.append(100.0 - _bounded_zscore(ser, int(p.window)))
    if not parts:
        raise ValueError("risk_appetite_index has no usable numeric values")
    return pd.concat(parts, axis=1).mean(axis=1)


def _zscore(series: pd.Series, n: int) -> pd.Series:
    mean = series.rolling(n, min_periods=n).mean()
    std = series.rolling(n, min_periods=n).std(ddof=0).replace(0, np.nan)
    return (series - mean) / std


def _safe_zscore(series: Optional[pd.Series], p: SentimentParams) -> pd.Series:
    if series is None or len(series.dropna()) < int(p.window):
        return pd.Series(dtype=float)
    return _zscore(series, int(p.window))


def _bounded_zscore(series: pd.Series, n: int) -> pd.Series:
    return (_zscore(series, n).clip(lower=-5.0, upper=5.0) + 5.0) / 10.0 * 100.0


def _composite(parts: List[pd.Series], *, invert: bool = False) -> pd.Series:
    usable = [ser for ser in parts if ser is not None and not ser.dropna().empty]
    if not usable:
        raise ValueError("composite sentiment has no usable numeric values")
    out = pd.concat(usable, axis=1).mean(axis=1)
    return -out if invert else out


def _direction(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value > 0:
        return "bullish"
    if value < 0:
        return "bearish"
    return "neutral"


def _sentiment_state(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value >= 50.0:
        return "euphoric"
    if value > 5.0:
        return "optimistic"
    if value <= -50.0:
        return "panic"
    if value < -5.0:
        return "pessimistic"
    return "neutral"


def _attention_state(value: Optional[float], p: SentimentParams) -> str:
    if value is None:
        return "unknown"
    if value >= float(p.high_percentile):
        return "high_attention"
    if value <= float(p.low_percentile):
        return "low_attention"
    return "normal_attention"


def _crowding_state(value: Optional[float], p: SentimentParams) -> str:
    if value is None:
        return "unknown"
    if value >= float(p.crowding_threshold):
        return "crowded"
    if value <= float(p.low_percentile):
        return "uncrowded"
    return "balanced"


def _fear_greed_state(value: Optional[float], p: SentimentParams) -> str:
    if value is None:
        return "unknown"
    if value <= float(p.fear_threshold):
        return "fear"
    if value >= float(p.greed_threshold):
        return "greed"
    return "neutral"


def _flow_state(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value > 0:
        return "inflow"
    if value < 0:
        return "outflow"
    return "neutral"


def _contrarian_state(sentiment: str, attention: str, fear_greed: str) -> str:
    if sentiment in {"euphoric", "optimistic"} and attention == "high_attention" and fear_greed == "greed":
        return "contrarian_bearish"
    if sentiment in {"panic", "pessimistic"} and attention == "high_attention" and fear_greed == "fear":
        return "contrarian_bullish"
    return "none"


def _risk_state(value: Optional[float], p: SentimentParams) -> str:
    if value is None:
        return "unknown"
    if value >= float(p.high_percentile):
        return "high"
    if value <= float(p.low_percentile):
        return "low"
    return "normal"


def _signal(sentiment: str, attention: str, crowding: str, fear_greed: str, flow: str) -> str:
    if sentiment in {"euphoric", "optimistic"} and flow == "inflow" and crowding != "crowded":
        return "risk_appetite_support"
    if sentiment in {"panic", "pessimistic"} or fear_greed == "fear":
        return "risk_aversion_pressure"
    if crowding == "crowded" and attention == "high_attention":
        return "crowding_warning"
    return "neutral"


def _normalized(series: pd.Series, p: SentimentParams) -> Optional[float]:
    valid = series.dropna()
    if len(valid) < 2:
        return None
    window = max(2, min(int(p.window), len(valid)))
    tail = valid.tail(window)
    low = tail.quantile(float(p.low_percentile) / 100.0)
    high = tail.quantile(float(p.high_percentile) / 100.0)
    if high == low:
        return None
    return float(((valid.iloc[-1] - low) / (high - low) * 100.0).clip(0.0, 100.0))


def _raw_to_frame(data: Any, extractor: Optional[ExtractorSpec]) -> ModuleResult[pd.DataFrame]:
    warnings: List[str] = []
    if extractor is not None and extractor.extractors:
        try:
            cols = {name: fn(data) for name, fn in extractor.extractors.items()}
            return ModuleResult.success(pd.DataFrame(cols), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("extractor_error", "extractor failed", details={"error": str(exc), "error_type": type(exc).__name__})
    if isinstance(data, pd.DataFrame):
        return ModuleResult.success(data.copy(), warnings=warnings)
    if isinstance(data, pd.Series):
        return ModuleResult.success(data.to_frame(name=data.name or "value").reset_index(drop=False), warnings=warnings)
    if isinstance(data, dict):
        try:
            if all(isinstance(v, IterableABC) and not isinstance(v, (str, bytes, dict)) for v in data.values()):
                return ModuleResult.success(pd.DataFrame(data), warnings=warnings)
            return ModuleResult.success(pd.DataFrame([data]), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("unsupported_input", "dict input could not be converted to DataFrame", details={"error": str(exc)})
    if isinstance(data, (list, tuple)):
        try:
            return ModuleResult.success(pd.DataFrame(data), warnings=warnings)
        except Exception as exc:
            return ModuleResult.fail("unsupported_input", "sequence input could not be converted to DataFrame", details={"error": str(exc)})
    return ModuleResult.fail("unsupported_input", f"unsupported_input: {type(data).__name__}; provide DataFrame, Series, list, dict, or ExtractorSpec")


def _find_any_col(cols: Dict[str, Any], names: List[str]) -> Optional[Any]:
    for name in names:
        if not name:
            continue
        if name in cols:
            return cols[name]
        lower = str(name).lower()
        for key, col in cols.items():
            if key.lower() == lower:
                return col
    return None


def _series_to_json(series: pd.Series) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for value in series.tolist():
        out.append(_safe_float(value))
    return out


def _last_float(series: Optional[pd.Series]) -> Optional[float]:
    if series is None:
        return None
    valid = series.replace([np.inf, -np.inf], np.nan).dropna()
    if valid.empty:
        return None
    return _safe_float(valid.iloc[-1])


def _safe_float(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except Exception:
        return None
    if not np.isfinite(num):
        return None
    return num


__all__ = ["SentimentParams", "SentimentReport", "normalize_sentiment_input", "run_sentiment_indicator", "SENTIMENT_INDICATORS"]
