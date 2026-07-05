"""Streaming content-addressed storage for opaque evidence artifacts."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from qst.canonical_json import stable_json_bytes
from qst.provenance import ArtifactDescriptor, artifact_identity, seal_artifact

DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024


def hash_stream(stream: BinaryIO, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> tuple[str, int]:
    """Hash a stream with bounded reads and return prefixed digest and size."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(chunk_size):
        digest.update(chunk)
        size += len(chunk)
    return f"sha256:{digest.hexdigest()}", size


class ContentAddressedStore:
    """Local immutable object store; it never interprets artifact bytes."""

    def __init__(self, root: Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.root = root.resolve()
        self.chunk_size = chunk_size
        self.objects = self.root / "objects" / "sha256"
        self.descriptors = self.root / "descriptors"
        self.objects.mkdir(parents=True, exist_ok=True)
        self.descriptors.mkdir(parents=True, exist_ok=True)

    def put_file(self, source: Path, *, media_type: str) -> ArtifactDescriptor:
        """Stream a file into the store, deduplicate it, and persist its descriptor."""

        source = source.resolve(strict=True)
        temporary: Path | None = None
        try:
            with source.open("rb") as input_stream, tempfile.NamedTemporaryFile(
                dir=self.root, delete=False
            ) as output_stream:
                temporary = Path(output_stream.name)
                digest = hashlib.sha256()
                size = 0
                while chunk := input_stream.read(self.chunk_size):
                    digest.update(chunk)
                    size += len(chunk)
                    output_stream.write(chunk)
                output_stream.flush()
                os.fsync(output_stream.fileno())
            hex_digest = digest.hexdigest()
            object_path = self.objects / hex_digest[:2] / hex_digest
            object_path.parent.mkdir(parents=True, exist_ok=True)
            if object_path.exists():
                with object_path.open("rb") as existing_stream:
                    existing_digest, existing_size = hash_stream(
                        existing_stream, chunk_size=self.chunk_size
                    )
                if existing_digest != f"sha256:{hex_digest}" or existing_size != size:
                    raise OSError(
                        "existing content-addressed object has unexpected digest or size"
                    )
                temporary.unlink()
                temporary = None
            else:
                os.replace(temporary, object_path)
                temporary = None
            descriptor = seal_artifact(
                ArtifactDescriptor(
                    media_type=media_type,
                    digest=f"sha256:{hex_digest}",
                    size=size,
                    uris=(f"qst-object://sha256/{hex_digest}",),
                )
            )
            self._write_descriptor(descriptor)
            return descriptor
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def put_bytes(self, payload: bytes, *, media_type: str) -> ArtifactDescriptor:
        """Store bounded in-memory output without requiring callers to manage temp files."""

        with tempfile.NamedTemporaryFile(dir=self.root, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            return self.put_file(temporary, media_type=media_type)
        finally:
            temporary.unlink(missing_ok=True)

    def object_path(self, descriptor: ArtifactDescriptor) -> Path:
        hex_digest = descriptor.digest.removeprefix("sha256:")
        return self.objects / hex_digest[:2] / hex_digest

    def verify(self, descriptor: ArtifactDescriptor) -> bool:
        if (
            descriptor.descriptor_id is None
            or descriptor.descriptor_id != artifact_identity(descriptor)
        ):
            return False
        path = self.object_path(descriptor)
        if not path.is_file():
            return False
        with path.open("rb") as stream:
            digest, size = hash_stream(stream, chunk_size=self.chunk_size)
        return digest == descriptor.digest and size == descriptor.size

    def descriptor_paths(self) -> tuple[Path, ...]:
        return tuple(sorted(self.descriptors.glob("*.json")))

    def _write_descriptor(self, descriptor: ArtifactDescriptor) -> None:
        if descriptor.descriptor_id is None:
            raise ValueError("descriptor must be sealed")
        path = self.descriptors / f"{descriptor.descriptor_id.removeprefix('sha256:')}.json"
        payload = stable_json_bytes(descriptor.model_dump(mode="json"))
        if path.exists() and path.read_bytes() != payload:
            raise OSError("descriptor identity collision")
        if not path.exists():
            path.write_bytes(payload)
