"""Convert supported QST strategy outputs into SignalFrame records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.artifacts.decimal_string import DecimalString, normalize_to_canonical
from quant_strategy_tokenizer.frames import MarketFrame, SignalFrame, SignalRow
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from quant_strategy_tokenizer.types.decision import (
    Accept,
    Decision,
    decision_to_dict,
    parse_decision,
)
from quant_strategy_tokenizer.types.plan import NoopPlan, OrderIntentPlan, Plan, parse_plan

DecisionToSignal = Literal["accept_as_long", "accept_short_split"]
PlanToSignal = Literal["order_intent_side", "noop_as_flat"]
MultiSymbolPolicy = Literal["long_format"]

_DECISION_KINDS = {"accept", "reject", "block", "abstain", "unknown", "error"}
_PLAN_KINDS = {"noop", "order_intent"}


class SignalExtractionPolicy(BaseModel):
    """Policy for mapping supported strategy outputs into long-format signals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_node_name: str = "plan"
    decision_to_signal: DecisionToSignal = "accept_as_long"
    plan_to_signal: PlanToSignal = "order_intent_side"
    score_threshold: float | None = None
    active_size: DecimalString = "1"
    market_external_name: str = "market"
    profile: ProfileLiteral = "research"
    multi_symbol_policy: MultiSymbolPolicy = "long_format"


def _frame_for_symbol(market: MarketFrame, symbol: str) -> tuple[pd.DataFrame, list[datetime]]:
    bars = [bar for bar in market.bars if bar.symbol == symbol]
    timestamps = [bar.timestamp for bar in bars]
    frame = pd.DataFrame(
        {
            "open": [float(bar.open) for bar in bars],
            "high": [float(bar.high) for bar in bars],
            "low": [float(bar.low) for bar in bars],
            "close": [float(bar.close) for bar in bars],
            "volume": [float(bar.volume) for bar in bars],
        },
        index=pd.DatetimeIndex(timestamps),
    )
    return frame, timestamps


def _output_kind(output: object) -> str | None:
    if isinstance(output, dict):
        kind = output.get("kind")
    else:
        kind = getattr(output, "kind", None)
    return kind if isinstance(kind, str) else None


def _decision_signal(decision: Decision, policy: SignalExtractionPolicy) -> tuple[str, str]:
    if not isinstance(decision, Accept):
        return "flat", "0"

    if policy.decision_to_signal == "accept_short_split":
        raw = decision_to_dict(decision)
        evidence = raw.get("evidence", {})
        if isinstance(evidence, dict):
            direction = evidence.get("direction", evidence.get("side"))
            if direction == "short":
                return "short", policy.active_size
    return "long", policy.active_size


def _plan_signal(plan: Plan) -> tuple[str, str]:
    if isinstance(plan, OrderIntentPlan):
        return plan.side, normalize_to_canonical(plan.sizing)
    if isinstance(plan, NoopPlan):
        return "flat", "0"
    raise TypeError(f"Unsupported Plan variant: {type(plan).__name__}")


def _single_point_row(
    *,
    timestamp: datetime,
    symbol: str,
    signal: str,
    size: str,
) -> SignalRow:
    return SignalRow(
        timestamp=timestamp,
        symbol=symbol,
        signal=signal,  # type: ignore[arg-type]
        size=size,
    )


def _is_bool_series(series: pd.Series) -> bool:
    if pd.api.types.is_bool_dtype(series.dtype):
        return True
    values = series.dropna().tolist()
    return bool(values) and all(isinstance(value, bool) for value in values)


def _is_numeric_series(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series.dtype) and not _is_bool_series(series)


def _series_timestamps(series: pd.Series, fallback: list[datetime]) -> list[datetime]:
    if isinstance(series.index, pd.DatetimeIndex):
        return [timestamp.to_pydatetime() for timestamp in series.index]
    if len(series) != len(fallback):
        raise TypeError("Series output has no DatetimeIndex and does not align with market bars")
    return fallback


def _bool_series_rows(
    series: pd.Series,
    *,
    symbol: str,
    fallback_timestamps: list[datetime],
    policy: SignalExtractionPolicy,
) -> list[SignalRow]:
    timestamps = _series_timestamps(series, fallback_timestamps)
    rows: list[SignalRow] = []
    for timestamp, value in zip(timestamps, series.fillna(False).astype(bool), strict=True):
        signal = "long" if bool(value) else "flat"
        size = policy.active_size if signal == "long" else "0"
        rows.append(_single_point_row(timestamp=timestamp, symbol=symbol, signal=signal, size=size))
    return rows


def _score_series_rows(
    series: pd.Series,
    *,
    symbol: str,
    fallback_timestamps: list[datetime],
    policy: SignalExtractionPolicy,
) -> list[SignalRow]:
    if policy.score_threshold is None:
        raise TypeError(
            "Unsupported output type for signal extraction: numeric TimeSeries requires "
            "SignalExtractionPolicy.score_threshold"
        )
    timestamps = _series_timestamps(series, fallback_timestamps)
    rows: list[SignalRow] = []
    for timestamp, value in zip(timestamps, pd.to_numeric(series, errors="coerce"), strict=True):
        active = bool(pd.notna(value) and float(value) >= policy.score_threshold)
        signal = "long" if active else "flat"
        size = policy.active_size if active else "0"
        rows.append(_single_point_row(timestamp=timestamp, symbol=symbol, signal=signal, size=size))
    return rows


def _extract_rows(
    output: object,
    *,
    symbol: str,
    timestamps: list[datetime],
    policy: SignalExtractionPolicy,
) -> list[SignalRow]:
    if not timestamps:
        return []

    kind = _output_kind(output)
    if kind in _PLAN_KINDS:
        signal, size = _plan_signal(parse_plan(output))
        return [
            _single_point_row(
                timestamp=timestamps[-1],
                symbol=symbol,
                signal=signal,
                size=size,
            )
        ]

    if kind in _DECISION_KINDS:
        signal, size = _decision_signal(parse_decision(output), policy)
        return [
            _single_point_row(
                timestamp=timestamps[-1],
                symbol=symbol,
                signal=signal,
                size=size,
            )
        ]

    if isinstance(output, pd.Series):
        if _is_bool_series(output):
            return _bool_series_rows(
                output,
                symbol=symbol,
                fallback_timestamps=timestamps,
                policy=policy,
            )
        if _is_numeric_series(output):
            return _score_series_rows(
                output,
                symbol=symbol,
                fallback_timestamps=timestamps,
                policy=policy,
            )

    raise TypeError(
        f"Unsupported output type for signal extraction: {type(output).__name__}. "
        "Supported: Decision / Plan / bool TimeSeries / score TimeSeries + threshold."
    )


def execute_to_signals(
    strategy_ir: StrategyIR,
    market: MarketFrame,
    *,
    policy: SignalExtractionPolicy | None = None,
    externals: dict[str, Any] | None = None,
) -> SignalFrame:
    """Execute a strategy against a MarketFrame and extract deterministic signals."""

    resolved_policy = policy or SignalExtractionPolicy()
    rows: list[SignalRow] = []

    for symbol in market.symbols:
        market_frame, timestamps = _frame_for_symbol(market, symbol)
        payload: dict[str, Any] = dict(externals or {})
        payload[resolved_policy.market_external_name] = market_frame
        payload.setdefault("state", {})
        payload.setdefault("sizing", 1.0)

        result = execute_strategy(
            strategy_ir,
            payload,
            profile=resolved_policy.profile,
        )
        if not result.ok:
            raise RuntimeError(
                f"Strategy execution failed during signal extraction: "
                f"{result.error or 'unknown_error'}"
            )
        if resolved_policy.output_node_name not in result.outputs:
            raise KeyError(
                f"Strategy output {resolved_policy.output_node_name!r} not found; "
                f"available outputs: {sorted(result.outputs)}"
            )
        rows.extend(
            _extract_rows(
                result.outputs[resolved_policy.output_node_name],
                symbol=symbol,
                timestamps=timestamps,
                policy=resolved_policy,
            )
        )

    return SignalFrame(symbols=market.symbols, rows=rows)
