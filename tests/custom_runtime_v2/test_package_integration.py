from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from quant_strategy_tokenizer.custom_runtime_v2 import load_token_pack
from quant_strategy_tokenizer.package import package_strategy, verify_package
from quant_strategy_tokenizer.tokens_v2 import token_pack_package_section_from_packs

ROOT = Path(__file__).resolve().parents[2]
PACK_DIR = ROOT / "tokenpacks" / "qst-tokenpack-kalman"


def test_qstpkg_verify_checks_token_packs_without_executing_code(tmp_path: Path) -> None:
    package_dir = tmp_path / "demo.qstpkg"
    package_strategy(ROOT / "strategies" / "kdj_cross_basic.qst.yaml", package_dir)
    embedded_dir = package_dir / "deps" / "tokenpacks" / "qst-tokenpack-kalman"
    shutil.copytree(PACK_DIR, embedded_dir)
    pack = load_token_pack(embedded_dir)
    _add_token_packs_section(package_dir, pack)

    result = verify_package(package_dir)

    assert result.ok


def test_qstpkg_verify_fails_token_pack_hash_mismatch(tmp_path: Path) -> None:
    package_dir = tmp_path / "demo.qstpkg"
    package_strategy(ROOT / "strategies" / "kdj_cross_basic.qst.yaml", package_dir)
    embedded_dir = package_dir / "deps" / "tokenpacks" / "qst-tokenpack-kalman"
    shutil.copytree(PACK_DIR, embedded_dir)
    pack = load_token_pack(embedded_dir)
    _add_token_packs_section(package_dir, pack)
    manifest_path = embedded_dir / "tokenpack.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tokens"][0]["risk"]["risk_level"] = "high"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_package(package_dir)

    assert not result.ok
    assert "QST_V2_PACKAGE_TOKEN_PACK_HASH_MISMATCH" in [failure.kind for failure in result.failures]


def _add_token_packs_section(package_dir: Path, pack: object) -> None:
    manifest_path = package_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["token_packs"] = token_pack_package_section_from_packs(
        (pack,),  # type: ignore[arg-type]
        embedded_policy="spec_and_source",
    ).model_dump(mode="json")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
