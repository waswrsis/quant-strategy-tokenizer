"""Rebuildable SQLite index for artifact descriptors."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from qst.provenance import ArtifactDescriptor


class ArtifactIndex:
    """A derived local index; descriptor JSON remains authoritative."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS artifacts (
                descriptor_id TEXT PRIMARY KEY,
                digest TEXT NOT NULL,
                media_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                descriptor_json TEXT NOT NULL
                )"""
            )

    def upsert(self, descriptor: ArtifactDescriptor) -> None:
        if descriptor.descriptor_id is None:
            raise ValueError("descriptor must be sealed")
        payload = descriptor.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO artifacts VALUES (?, ?, ?, ?, ?)",
                (
                    descriptor.descriptor_id,
                    descriptor.digest,
                    descriptor.media_type,
                    descriptor.size,
                    payload,
                ),
            )

    def get(self, descriptor_id: str) -> ArtifactDescriptor | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT descriptor_json FROM artifacts WHERE descriptor_id = ?", (descriptor_id,)
            ).fetchone()
        return None if row is None else ArtifactDescriptor.model_validate_json(row[0])

    def rebuild(self, descriptor_paths: tuple[Path, ...]) -> int:
        descriptors = [
            ArtifactDescriptor.model_validate(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(descriptor_paths)
        ]
        with self._connect() as connection:
            connection.execute("DELETE FROM artifacts")
        for descriptor in descriptors:
            self.upsert(descriptor)
        return len(descriptors)

    def journal_mode(self) -> str:
        with self._connect() as connection:
            row = connection.execute("PRAGMA journal_mode").fetchone()
        return str(row[0]).lower()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

