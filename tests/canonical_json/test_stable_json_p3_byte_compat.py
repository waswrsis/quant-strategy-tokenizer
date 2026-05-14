from __future__ import annotations

from quant_strategy_tokenizer.canonical_json import stable_json_bytes
from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes


def test_stable_json_bytes_match_p3_lock_bytes() -> None:
    fixtures = [
        {"b": [2, {"d": None, "c": True}], "a": "x"},
        {
            "lock_version": "qst-lock/0.1",
            "strategy_hashes": {
                "instance_hash": "sha256:" + "1" * 64,
                "graph_hash": "sha256:" + "2" * 64,
                "param_hash": "sha256:" + "3" * 64,
            },
            "tagspecs": [{"semantic_id": "indicator.ewm", "version": 1}],
        },
    ]

    for fixture in fixtures:
        assert stable_json_bytes(fixture) == canonical_lock_bytes(fixture)


def test_p3_byte_shape_is_unchanged_for_existing_fixture() -> None:
    payload = {"b": [2, {"d": None, "c": True}], "a": "x"}

    assert stable_json_bytes(payload) == b'{"a":"x","b":[2,{"c":true,"d":null}]}'
