from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar
from quant_strategy_tokenizer.ir.model import ExternalSpec, GraphNode, StrategyIR
from quant_strategy_tokenizer.runtime.signal_extraction import (
    SignalExtractionPolicy,
    execute_to_signals,
)


def _market(symbols: list[str] | None = None) -> MarketFrame:
    selected = symbols or ["BTC/USDT"]
    timestamps = [
        datetime(2026, 5, 14, 0, 0, tzinfo=UTC),
        datetime(2026, 5, 14, 0, 1, tzinfo=UTC),
    ]
    bars: list[OHLCVBar] = []
    for symbol in selected:
        bars.extend(
            [
                OHLCVBar(
                    timestamp=timestamps[0],
                    symbol=symbol,
                    open="10",
                    high="12",
                    low="9",
                    close="11",
                    volume="100",
                ),
                OHLCVBar(
                    timestamp=timestamps[1],
                    symbol=symbol,
                    open="12",
                    high="13",
                    low="10",
                    close="11",
                    volume="100",
                ),
            ]
        )
    return MarketFrame(symbols=selected, bars=bars)


def _externals() -> dict[str, ExternalSpec]:
    return {"market": ExternalSpec(type="Frame[OHLCV]", required=True)}


def _bool_strategy() -> StrategyIR:
    return StrategyIR(
        strategy="bool_signal",
        externals=_externals(),
        graph=[
            GraphNode(
                id="signal",
                token="compare.gt",
                inputs={"a": "$externals.market.close", "b": "$externals.market.open"},
            )
        ],
        outputs={"signal": "signal.value"},
    )


def _decision_strategy() -> StrategyIR:
    return StrategyIR(
        strategy="decision_signal",
        externals=_externals(),
        graph=[
            GraphNode(
                id="cmp",
                token="compare.gt",
                inputs={"a": "$externals.market.close", "b": "$externals.market.open"},
            ),
            GraphNode(
                id="decision",
                token="decision.lift_bool",
                params={"accept_reason": "entry", "reject_reason": "no_entry"},
                inputs={"series": "cmp.value"},
            ),
        ],
        outputs={"decision": "decision.decision"},
    )


def _plan_strategy() -> StrategyIR:
    return StrategyIR(
        strategy="plan_signal",
        externals={
            **_externals(),
            "sizing": ExternalSpec(type="Number", required=True),
        },
        graph=[
            GraphNode(
                id="cmp",
                token="compare.gt",
                inputs={"a": "$externals.market.close", "b": "$externals.market.open"},
            ),
            GraphNode(
                id="decision",
                token="decision.lift_bool",
                params={"accept_reason": "entry", "reject_reason": "no_entry"},
                inputs={"series": "cmp.value"},
            ),
            GraphNode(
                id="plan",
                token="plan.order_intent",
                params={"side": "long"},
                inputs={"decision": "decision.decision", "sizing": "$externals.sizing"},
            ),
        ],
        outputs={"plan": "plan.plan"},
    )


def _score_strategy() -> StrategyIR:
    return StrategyIR(
        strategy="score_signal",
        externals=_externals(),
        graph=[
            GraphNode(
                id="score",
                token="math.add",
                inputs={"a": "$externals.market.close", "b": "$externals.market.open"},
            )
        ],
        outputs={"score": "score.value"},
    )


def test_execute_to_signals_from_decision_output() -> None:
    signals = execute_to_signals(
        _decision_strategy(),
        _market(),
        policy=SignalExtractionPolicy(output_node_name="decision", active_size="2"),
    )

    assert [(row.signal, row.size) for row in signals.rows] == [("flat", "0")]
    assert signals.rows[0].timestamp == datetime(2026, 5, 14, 0, 1, tzinfo=UTC)


def test_execute_to_signals_from_plan_output_order_intent() -> None:
    market = _market()
    market.bars[1].close = "13"

    signals = execute_to_signals(_plan_strategy(), market)

    assert [(row.signal, row.size) for row in signals.rows] == [("long", "1")]


def test_execute_to_signals_from_bool_timeseries_multi_symbol_long_format() -> None:
    signals = execute_to_signals(
        _bool_strategy(),
        _market(["ETH/USDT", "BTC/USDT"]),
        policy=SignalExtractionPolicy(output_node_name="signal", active_size="3"),
    )

    assert signals.symbols == ["BTC/USDT", "ETH/USDT"]
    assert [(row.timestamp, row.symbol, row.signal, row.size) for row in signals.rows] == [
        (datetime(2026, 5, 14, 0, 0, tzinfo=UTC), "BTC/USDT", "long", "3"),
        (datetime(2026, 5, 14, 0, 0, tzinfo=UTC), "ETH/USDT", "long", "3"),
        (datetime(2026, 5, 14, 0, 1, tzinfo=UTC), "BTC/USDT", "flat", "0"),
        (datetime(2026, 5, 14, 0, 1, tzinfo=UTC), "ETH/USDT", "flat", "0"),
    ]


def test_execute_to_signals_from_score_timeseries_with_threshold() -> None:
    signals = execute_to_signals(
        _score_strategy(),
        _market(),
        policy=SignalExtractionPolicy(output_node_name="score", score_threshold=22),
    )

    assert [(row.signal, row.size) for row in signals.rows] == [("flat", "0"), ("long", "1")]


def test_execute_to_signals_rejects_pure_numeric_series_without_threshold() -> None:
    with pytest.raises(TypeError, match="score_threshold"):
        execute_to_signals(
            _score_strategy(),
            _market(),
            policy=SignalExtractionPolicy(output_node_name="score"),
        )


def test_execute_to_signals_raises_on_runtime_failure() -> None:
    broken = StrategyIR(
        strategy="broken",
        externals=_externals(),
        graph=[
            GraphNode(
                id="score",
                token="data.column",
                params={"column": "missing"},
                inputs={"frame": "$externals.market"},
            )
        ],
        outputs={"score": "score.value"},
    )

    with pytest.raises(RuntimeError, match="Strategy execution failed"):
        execute_to_signals(
            broken,
            _market(),
            policy=SignalExtractionPolicy(output_node_name="score", score_threshold=1),
        )
