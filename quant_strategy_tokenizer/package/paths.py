"""Package path helpers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


def safe_join(root: Path, relative_path: str) -> Path:
    """Resolve a manifest-relative path while rejecting absolute/up-level paths."""

    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"Unsafe package path: {relative_path!r}")
    return root.joinpath(*pure.parts)


def to_posix_relative(path: Path, root: Path) -> str:
    """Return a POSIX relative path for manifest storage."""

    return path.relative_to(root).as_posix()
