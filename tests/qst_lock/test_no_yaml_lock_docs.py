from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_docs_do_not_define_yaml_lock_examples() -> None:
    offenders: list[str] = []
    for path in (ROOT / "docs").rglob("*"):
        if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "qst.lock:" in text or "lock_version: qst-lock" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
