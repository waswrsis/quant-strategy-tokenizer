from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from tests.helpers import load_sample_market

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_duplicate_chain_execute_records_cache_hits() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "uses_cse_duplicate_chain.qst.yaml")
    market = load_sample_market(ROOT / "examples" / "sample_market_btc_15m.csv")

    result = execute_strategy(ir, {"market": market})

    assert result.ok
    assert "value" in result.outputs
    cache_hits = [node for node in result.trace.nodes if node.cache_hit]
    assert len(cache_hits) == 2
    assert cache_hits[0].reused_from == "n0"
    assert cache_hits[0].fingerprint == result.trace.nodes[0].fingerprint
    assert cache_hits[1].reused_from == "n2"
    assert cache_hits[1].fingerprint == result.trace.nodes[2].fingerprint


def test_p0_reference_trace_node_count_remains_compatible() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    market = load_sample_market(ROOT / "examples" / "sample_market_btc_15m.csv")

    result = execute_strategy(ir, {"market": market})

    assert result.ok
    assert len(result.trace.nodes) == 13


def test_qst_fingerprint_outputs_plan_debug_json() -> None:
    result = runner.invoke(
        app,
        ["fingerprint", str(ROOT / "strategies" / "uses_cse_duplicate_chain.qst.yaml")],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["hashes"]["instance_hash"].startswith("sha256:")
    assert len(payload["fingerprints"]) == 5
    assert payload["reuse_pairs"]
    assert payload["reuse_pairs"][0]["reused_from"] == "n0"


def test_qst_execute_trace_file_contains_cache_hit_fields(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"

    result = runner.invoke(
        app,
        [
            "execute",
            str(ROOT / "strategies" / "uses_cse_duplicate_chain.qst.yaml"),
            "--market",
            str(ROOT / "examples" / "sample_market_btc_15m.csv"),
            "--trace-path",
            str(trace_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    assert any(node["cache_hit"] for node in payload["nodes"])
    assert any(node["fingerprint"].startswith("fp_sha256:") for node in payload["nodes"])
