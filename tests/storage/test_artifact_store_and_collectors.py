from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest

from qst.collectors import transition_activity, verified_result_evidence
from qst.provenance import ActivityRecord, seal_activity
from qst.storage import ArtifactIndex, ContentAddressedStore, hash_stream

NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class GuardedStream(BytesIO):
    def __init__(self, value: bytes, limit: int) -> None:
        super().__init__(value)
        self.limit = limit
        self.maximum_read = 0

    def read(self, size: int = -1) -> bytes:
        assert 0 < size <= self.limit
        self.maximum_read = max(self.maximum_read, size)
        return super().read(size)


def test_hash_stream_uses_bounded_chunks() -> None:
    stream = GuardedStream(b"x" * 10000, 1024)
    digest, size = hash_stream(stream, chunk_size=1024)
    assert digest.startswith("sha256:")
    assert size == 10000
    assert stream.maximum_read == 1024


def test_store_deduplicates_verifies_and_rejects_tampering(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"financial evidence")
    store = ContentAddressedStore(tmp_path / "store", chunk_size=8)
    first = store.put_file(source, media_type="application/octet-stream")
    second = store.put_file(source, media_type="application/octet-stream")
    assert first == second
    assert len(tuple(path for path in (store.root / "objects").rglob("*") if path.is_file())) == 1
    assert store.verify(first)
    store.object_path(first).write_bytes(b"tampered")
    assert not store.verify(first)


def test_sqlite_index_is_wal_and_rebuildable(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    store = ContentAddressedStore(tmp_path / "store")
    descriptor = store.put_file(source, media_type="text/csv")
    index = ArtifactIndex(tmp_path / "index.sqlite")
    assert index.journal_mode() == "wal"
    assert index.rebuild(store.descriptor_paths()) == 1
    assert index.get(descriptor.descriptor_id) == descriptor


def test_collector_state_machine_and_verified_evidence(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text('{"metric":1}', encoding="utf-8")
    descriptor = ContentAddressedStore(tmp_path / "store").put_file(
        source, media_type="application/json"
    )
    discovered = seal_activity(
        ActivityRecord(activity_type="finrl.training", status="discovered", started_at=NOW)
    )
    collecting = transition_activity(discovered, "collecting", at=NOW)
    complete = transition_activity(
        collecting,
        "complete",
        at=NOW,
        output_artifact_ids=(descriptor.descriptor_id,),
    )
    verified = transition_activity(complete, "verified", at=NOW)
    evidence = verified_result_evidence(
        verified, (descriptor,), subject_ref="finrl-run:1", observed_at=NOW
    )
    assert evidence.payload.kind == "result"
    assert evidence.payload.collection_status == "verified"


def test_collector_rejects_skip_terminal_and_unstable_artifacts(tmp_path: Path) -> None:
    discovered = seal_activity(
        ActivityRecord(activity_type="external.run", status="discovered", started_at=NOW)
    )
    with pytest.raises(ValueError, match="invalid activity transition"):
        transition_activity(discovered, "verified", at=NOW)
    collecting = transition_activity(discovered, "collecting", at=NOW)
    complete = transition_activity(
        collecting, "complete", at=NOW, output_artifact_ids=("sha256:" + "a" * 64,)
    )
    verified = transition_activity(complete, "verified", at=NOW)
    with pytest.raises(ValueError, match="artifact set"):
        verified_result_evidence(verified, (), subject_ref="run:1", observed_at=NOW)
