from __future__ import annotations

from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar, compute_frame_hash


def test_frame_hash_excludes_frame_hash_field() -> None:
    frame = MarketFrame(
        bars=[
            OHLCVBar(
                timestamp="2026-05-14T09:00:00Z",
                symbol="BTC/USD",
                open="1",
                high="2",
                low="0.5",
                close="1.5",
                volume="10",
            )
        ]
    )
    baseline = compute_frame_hash(frame)

    same = frame.model_copy(update={"frame_hash": "sha256:" + "f" * 64})
    assert compute_frame_hash(same) == baseline


def test_frame_hash_is_stable_across_input_order() -> None:
    first = MarketFrame(
        symbols=["ETH/USD", "BTC/USD"],
        bars=[
            OHLCVBar(timestamp="2026-05-14T10:00:00Z", symbol="ETH/USD", open="1", high="2", low="1", close="2", volume="3"),
            OHLCVBar(timestamp="2026-05-14T09:00:00Z", symbol="BTC/USD", open="1", high="2", low="1", close="2", volume="3"),
        ],
    )
    second = MarketFrame(
        symbols=["BTC/USD", "ETH/USD"],
        bars=[
            OHLCVBar(timestamp="2026-05-14T09:00:00Z", symbol="BTC/USD", open="1", high="2", low="1", close="2", volume="3"),
            OHLCVBar(timestamp="2026-05-14T10:00:00Z", symbol="ETH/USD", open="1", high="2", low="1", close="2", volume="3"),
        ],
    )

    assert compute_frame_hash(first) == compute_frame_hash(second)
