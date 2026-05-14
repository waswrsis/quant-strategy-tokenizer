from __future__ import annotations

import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ALLOWED_YAML_PATTERNS = (
    # Strategy and envelope YAML files are not lock files.
    "strategies/*.qst.yaml",
    "strategies/*.envelope.yaml",
    "tests/**/*.qst.yaml",
    "tests/**/*.envelope.yaml",
    # TagSpec, contract, and generated recipe YAML files are separate formats.
    "docs/tagspecs/*.yaml",
    "docs/contracts/*.yaml",
    "**/recipes/**/*.recipe.yaml",
    # P3a-1 package manifests are YAML by design; qst.lock remains JSON.
    "**/*.qstpkg/manifest.yaml",
    "**/*.qstpkg/fixtures/manifest.yaml",
    "**/*.qstpkg/strategies/*.envelope.yaml",
    # Engineering configuration YAML files are not lock files.
    ".github/workflows/*.yaml",
    ".github/workflows/*.yml",
    # Catch-all for Strategy IR YAML examples.
    "**/*.qst.yaml",
)

LOCK_STYLE_INDICATORS = ("lock_version:", "qst_version_policy:")


def _is_allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in ALLOWED_YAML_PATTERNS)


def test_docs_do_not_define_yaml_lock_examples() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        if path.suffix.lower() in {".yaml", ".yml"} and _is_allowed(path):
            continue
        text = path.read_text(encoding="utf-8")
        for indicator in LOCK_STYLE_INDICATORS:
            if indicator in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()}: {indicator}")

    assert offenders == []
