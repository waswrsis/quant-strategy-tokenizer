from __future__ import annotations

import math

import pytest

from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes


def test_canonical_lock_bytes_are_order_stable() -> None:
    left = {"b": [2, {"d": None, "c": True}], "a": "x"}
    right = {"a": "x", "b": [2, {"c": True, "d": None}]}

    assert canonical_lock_bytes(left) == canonical_lock_bytes(right)
    assert canonical_lock_bytes(left) == b'{"a":"x","b":[2,{"c":true,"d":null}]}'


@pytest.mark.parametrize(
    "value",
    [
        {"x": math.nan},
        {"x": math.inf},
        {"x": b"bytes"},
        {"x": (1, 2)},
        {1: "non-string-key"},
        {"x": object()},
    ],
)
def test_canonical_lock_bytes_reject_invalid_json_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        canonical_lock_bytes(value)


def test_canonical_lock_bytes_reject_depth_over_eight() -> None:
    value: object = "leaf"
    for _ in range(10):
        value = {"x": value}

    with pytest.raises(ValueError, match="depth"):
        canonical_lock_bytes(value)
