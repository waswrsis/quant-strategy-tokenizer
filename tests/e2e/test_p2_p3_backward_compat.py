from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
KDJ = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
P1 = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
EWM = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
runner = CliRunner()


def test_p2_provenance_and_hashes_remain_unchanged() -> None:
    canonical = canonicalize(load_strategy_file(EWM))
    provenance_nodes = [node for node in canonical.graph if node.provenance]

    assert provenance_nodes
    assert {tag.semantic_id for node in provenance_nodes for tag in node.provenance} == {
        "indicator.ewm"
    }
    assert compute_hashes(load_strategy_file(KDJ)).instance_hash == (
        "sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d"
    )
    assert compute_hashes(load_strategy_file(P1)).instance_hash == (
        "sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3"
    )


def test_p2_p3_cli_smoke_paths_remain_available(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    fork_path = tmp_path / "kdj_variant.qst.yaml"

    assert runner.invoke(app, ["tag", "verify", "docs/tagspecs/indicator.ewm.tagspec.yaml"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            [
                "recipe",
                "expand",
                "signals.dual_ema_cross",
                "--params",
                '{"fast_span":9,"slow_span":21}',
                "--output",
                str(tmp_path / "dual_ema.json"),
            ],
        ).exit_code
        == 0
    )
    assert runner.invoke(app, ["fingerprint", str(EWM)]).exit_code == 0
    assert runner.invoke(app, ["kernel", "plan", str(EWM)]).exit_code == 0
    assert runner.invoke(app, ["package", str(EWM), "--output", str(package_dir)]).exit_code == 0
    assert runner.invoke(app, ["verify", str(package_dir)]).exit_code == 0
    assert runner.invoke(app, ["search", "tagspec", "--fully-verified"]).exit_code == 0
    forked = runner.invoke(app, ["fork", str(KDJ), "--new-id", "kdj_variant", "--out", str(fork_path)])
    assert forked.exit_code == 0, forked.output

    assert load_strategy_file(fork_path).ir_version == "qst-ir/0.3.1"


def test_no_auto_upgrade_still_holds_for_non_fork_p3_commands(tmp_path: Path) -> None:
    lock_path = tmp_path / "qst.lock"
    canonical_path = tmp_path / "canonical.json"
    package_dir = tmp_path / "uses_ewm.qstpkg"

    lock_result = runner.invoke(
        app,
        ["lock", str(EWM), "--output", str(lock_path), "--canonical-output", str(canonical_path)],
    )
    package_result = runner.invoke(app, ["package", str(EWM), "--output", str(package_dir)])

    assert lock_result.exit_code == 0, lock_result.output
    assert package_result.exit_code == 0, package_result.output
    assert json.loads(canonical_path.read_text(encoding="utf-8"))["ir_version"] == "qst-ir/0.3"
    assert json.loads((package_dir / "strategies" / "canonical.json").read_text(encoding="utf-8"))[
        "ir_version"
    ] == "qst-ir/0.3"
