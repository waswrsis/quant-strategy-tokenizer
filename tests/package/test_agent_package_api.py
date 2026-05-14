from __future__ import annotations

from pathlib import Path

import quant_strategy_tokenizer.agent as agent

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def test_agent_package_api_roundtrip(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    unpacked_dir = tmp_path / "unpacked"

    built = agent.package(str(STRATEGY), str(package_dir))
    verified = agent.verify_package(str(package_dir))
    unpacked = agent.unpack(str(package_dir), str(unpacked_dir))

    assert built.manifest.package_version == "qstpkg/0.1"
    assert verified.ok
    assert verified.verification_level.value == "STRUCTURAL"
    assert unpacked.root == unpacked_dir


def test_agent_discover_lists_p3a1_api_surface() -> None:
    discovered = agent.discover()
    api = discovered["agent_api"]
    cli = discovered["cli_commands"]

    assert isinstance(api, dict)
    assert {"package", "unpack", "verify_package"} <= set(api["p3"])
    assert isinstance(cli, dict)
    assert {"package", "unpack", "verify"} <= set(cli["p3"])
