from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.package import package_strategy, read_package, unpack_package

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def test_unpack_copies_package_structure(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    unpacked_dir = tmp_path / "unpacked"

    package_strategy(STRATEGY, package_dir)
    unpacked = unpack_package(package_dir, unpacked_dir)

    assert unpacked.root == unpacked_dir
    assert (unpacked_dir / "manifest.yaml").exists()
    assert (unpacked_dir / "qst.lock").exists()
    assert (unpacked_dir / "strategies" / "source.qst.yaml").exists()
    assert read_package(unpacked_dir).manifest == read_package(package_dir).manifest


def test_package_output_dir_must_be_empty(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_dir.mkdir()
    (package_dir / "existing.txt").write_text("x", encoding="utf-8")

    try:
        package_strategy(STRATEGY, package_dir)
    except FileExistsError as exc:
        assert "not empty" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")
