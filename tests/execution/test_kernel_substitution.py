from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.composition.verifier import upgrade_verification
from quant_strategy_tokenizer.execution.kernel import (
    kernel_eligibility_for_node,
    make_kernel_plan_report,
)
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.provenance import ProvenanceTag
from quant_strategy_tokenizer.provenance.registry import load_tagspec_file
from quant_strategy_tokenizer.provenance.spec import VerificationStatus
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from tests.helpers import load_sample_market

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
runner = CliRunner()


def _canonical_ewm_node():
    canonical = canonicalize(load_strategy_file(STRATEGY))
    return next(node for node in canonical.graph if node.provenance)


def test_fully_verified_indicator_ewm_node_is_kernel_eligible() -> None:
    canonical = canonicalize(load_strategy_file(STRATEGY))

    report = make_kernel_plan_report(canonical)
    eligible = [node for node in report.nodes if node.eligible]

    assert report.eligible_count == 1
    assert eligible[0].semantic_id == "indicator.ewm"
    assert eligible[0].kernel_id == "builtin.indicator_ewm_v1_fastpath"


def test_default_execute_does_not_substitute_kernel() -> None:
    ir = load_strategy_file(STRATEGY)
    market = load_sample_market(MARKET)

    result = execute_strategy(ir, {"market": market})

    assert result.ok
    assert all(not node.kernel_substituted for node in result.trace.nodes)


def test_opt_in_kernel_substitution_matches_default_outputs() -> None:
    ir = load_strategy_file(STRATEGY)
    market = load_sample_market(MARKET)

    default = execute_strategy(ir, {"market": market})
    substituted = execute_strategy(ir, {"market": market}, kernel_substitution=True)

    assert default.ok
    assert substituted.ok
    assert substituted.trace.outputs == default.trace.outputs
    kernel_nodes = [node for node in substituted.trace.nodes if node.kernel_substituted]
    assert len(kernel_nodes) == 1
    assert kernel_nodes[0].kernel_id == "builtin.indicator_ewm_v1_fastpath"
    assert kernel_nodes[0].semantic_id == "indicator.ewm"


def test_non_indicator_provenance_is_not_kernel_eligible() -> None:
    node = _canonical_ewm_node().model_copy(
        update={
            "provenance": [
                ProvenanceTag(
                    semantic_id="indicator.rma",
                    version=1,
                    params={"alpha": 0.5, "init": "first_value"},
                    role="rma",
                    tag_attached_by="recipe_compiler",
                )
            ]
        }
    )

    decision = kernel_eligibility_for_node(node)

    assert not decision.eligible
    assert decision.blocked_reasons == ["unsupported_semantic"]


def test_unverified_tagspec_is_not_kernel_eligible(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    node = _canonical_ewm_node()
    unverified = VerificationStatus(
        tag_attached_by_trusted=True,
        graph_template_hash_valid=True,
        namespace_allowed=True,
    )

    monkeypatch.setattr(
        "quant_strategy_tokenizer.execution.kernel.upgrade_verification",
        lambda spec: spec.model_copy(update={"verification": unverified}),
    )

    decision = kernel_eligibility_for_node(node)

    assert not decision.eligible
    assert "tagspec_not_fully_verified" in decision.blocked_reasons


def test_tagspec_without_allowed_kernel_is_not_eligible(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    node = _canonical_ewm_node()
    spec = load_tagspec_file("docs/tagspecs/indicator.ewm.tagspec.yaml").model_copy(
        update={"allowed_kernels": []}
    )

    class RegistryStub:
        def get(self, semantic_id: str, version: int = 1):
            assert semantic_id == "indicator.ewm"
            assert version == 1
            return spec

    monkeypatch.setattr(
        "quant_strategy_tokenizer.execution.kernel.get_tagspec_registry",
        lambda: RegistryStub(),
    )

    decision = kernel_eligibility_for_node(node)

    assert not decision.eligible
    assert "kernel_not_allowed_by_tagspec" in decision.blocked_reasons


def test_kernel_substitution_does_not_change_hashes_or_canonical_json(tmp_path: Path) -> None:
    ir = load_strategy_file(STRATEGY)
    canonical = canonicalize(ir)
    before_hashes = compute_hashes(canonical)
    before_json = to_json(canonical)
    market = load_sample_market(MARKET)

    trace_path = tmp_path / "trace.json"
    result = execute_strategy(
        ir,
        {"market": market},
        kernel_substitution=True,
        trace_path=trace_path,
    )

    assert result.ok
    assert compute_hashes(canonical) == before_hashes
    assert to_json(canonical) == before_json


def test_qst_kernel_plan_outputs_eligible_kernel() -> None:
    result = runner.invoke(app, ["kernel", "plan", str(STRATEGY)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["eligible_count"] == 1
    assert payload["nodes"][0]["kernel_id"] == "builtin.indicator_ewm_v1_fastpath"


def test_qst_execute_kernel_substitution_writes_trace_evidence(tmp_path: Path) -> None:
    trace_path = tmp_path / "kernel_trace.json"

    result = runner.invoke(
        app,
        [
            "execute",
            str(STRATEGY),
            "--market",
            str(MARKET),
            "--kernel-substitution",
            "--trace-path",
            str(trace_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    kernel_nodes = [node for node in payload["nodes"] if node["kernel_substituted"]]
    assert len(kernel_nodes) == 1
    assert kernel_nodes[0]["kernel_id"] == "builtin.indicator_ewm_v1_fastpath"
    assert kernel_nodes[0]["semantic_id"] == "indicator.ewm"


def test_agent_kernel_plan_and_execute_kernel_substitution() -> None:
    ir = load_strategy_file(STRATEGY)
    market = load_sample_market(MARKET)

    report = agent.kernel_plan(ir)
    result = agent.execute(ir, {"market": market}, kernel_substitution=True)

    assert report.eligible_count == 1
    assert result.ok
    assert any(node.kernel_substituted for node in result.trace.nodes)


def test_full_tagspec_verification_allows_kernel_without_changing_verification() -> None:
    spec = load_tagspec_file("docs/tagspecs/indicator.ewm.tagspec.yaml")
    upgraded = upgrade_verification(spec)

    assert upgraded.verification.fully_verified is True
    assert upgraded.allowed_kernels[0]["kernel_id"] == "builtin.indicator_ewm_v1_fastpath"
