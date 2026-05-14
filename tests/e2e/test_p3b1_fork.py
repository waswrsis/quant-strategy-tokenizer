from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
runner = CliRunner()


def test_agent_fork_outputs_031_and_keeps_parent_unchanged() -> None:
    parent = load_strategy_file(STRATEGY)
    parent_hashes = compute_hashes(parent)

    forked = agent.fork(parent, "kdj_variant")

    assert parent.ir_version == "qst-ir/0.3"
    assert parent.derived_from is None
    assert forked.ir_version == "qst-ir/0.3.1"
    assert forked.strategy == "kdj_variant"
    assert forked.strategy_version == 1
    assert forked.derived_from is not None
    assert forked.derived_from.parent_strategy == parent.strategy
    assert forked.derived_from.parent_instance_hash == parent_hashes.instance_hash
    assert forked.derived_from.mutation_chain == []


def test_qst_fork_writes_yaml_with_031(tmp_path: Path) -> None:
    output = tmp_path / "kdj_variant.qst.yaml"

    result = runner.invoke(
        app,
        ["fork", str(STRATEGY), "--new-id", "kdj_variant", "--out", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    raw = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["ir_version"] == "qst-ir/0.3.1"
    assert raw["ir_version"] == "qst-ir/0.3.1"
    assert raw["derived_from"]["parent_instance_hash"].startswith("sha256:")


def test_qst_fork_records_parent_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "parent.qstpkg"
    output = tmp_path / "forked.qst.yaml"
    packaged = runner.invoke(app, ["package", str(STRATEGY), "--output", str(package_dir)])
    assert packaged.exit_code == 0, packaged.output

    result = runner.invoke(
        app,
        [
            "fork",
            str(STRATEGY),
            "--new-id",
            "kdj_variant",
            "--out",
            str(output),
            "--parent-package",
            str(package_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    raw = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert raw["derived_from"]["parent_package"] == str(package_dir)
    assert raw["derived_from"]["parent_package_version"] == "qstpkg/0.1"


def test_p0_p1_hashes_unchanged_after_p3b1_schema() -> None:
    p0_hashes = compute_hashes(load_strategy_file(STRATEGY))
    p1_hashes = compute_hashes(load_strategy_file(P1_STRATEGY))

    assert p0_hashes.graph_hash == "sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947"
    assert p0_hashes.param_hash == "sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28"
    assert p0_hashes.instance_hash == "sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d"
    assert p1_hashes.graph_hash == "sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa"
    assert p1_hashes.param_hash == "sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321"
    assert p1_hashes.instance_hash == "sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3"
