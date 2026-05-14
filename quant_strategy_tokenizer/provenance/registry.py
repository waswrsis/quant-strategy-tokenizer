"""TagSpec registry."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from quant_strategy_tokenizer.provenance.attachment import verify_tag_spec
from quant_strategy_tokenizer.provenance.spec import TagSpec


class TagSpecRegistry:
    """In-memory registry for built-in TagSpecs."""

    def __init__(self) -> None:
        self._specs: dict[tuple[str, int], TagSpec] = {}

    def register(self, spec: TagSpec) -> None:
        key = (spec.semantic_id, spec.version)
        if key in self._specs:
            raise ValueError(f"TagSpec {spec.semantic_id}/v{spec.version} already registered")
        self._specs[key] = spec

    def get(self, semantic_id: str, version: int = 1) -> TagSpec:
        try:
            return self._specs[(semantic_id, version)]
        except KeyError:
            raise KeyError(f"TagSpec {semantic_id}/v{version} not found") from None

    def list_specs(self) -> list[TagSpec]:
        return list(self._specs.values())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_tagspec_file(path: Path) -> TagSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("TagSpec YAML must contain a mapping")
    return verify_tag_spec(TagSpec.model_validate(raw))


@lru_cache(maxsize=1)
def get_tagspec_registry() -> TagSpecRegistry:
    registry = TagSpecRegistry()
    tagspec_dir = _repo_root() / "docs" / "tagspecs"
    if tagspec_dir.exists():
        for path in sorted(tagspec_dir.glob("*.yaml")):
            registry.register(load_tagspec_file(path))
    return registry
