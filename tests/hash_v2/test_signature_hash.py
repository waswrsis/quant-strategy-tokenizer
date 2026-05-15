from __future__ import annotations

from quant_strategy_tokenizer.hash_v2 import signature_hash_v2


def test_signature_hash_supports_empty_payload() -> None:
    assert signature_hash_v2() == signature_hash_v2({})


def test_signature_hash_is_deterministic() -> None:
    left = signature_hash_v2({"outputs": ["b", "a"], "inputs": {"x": "series"}})
    right = signature_hash_v2({"inputs": {"x": "series"}, "outputs": ["b", "a"]})

    assert left == right
