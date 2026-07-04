"""Deterministic persistence and lookup for authority policy profiles."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import yaml

from qst.canonical_json import stable_json_bytes

from .policy import (
    AuthorityPolicyProfile,
    authority_policy_profile_identity,
    controlled_release_profile,
    record_capture_profile,
    research_advisory_profile,
    seal_authority_policy_profile,
    strict_governance_profile,
)

MAX_PROFILE_BYTES = 1_048_576
PROFILE_SUFFIXES = {".json", ".yaml", ".yml"}


def builtin_authority_profiles() -> tuple[AuthorityPolicyProfile, ...]:
    return tuple(
        sorted(
            (
                record_capture_profile(),
                research_advisory_profile(),
                controlled_release_profile(),
                strict_governance_profile(),
            ),
            key=lambda item: item.profile_id,
        )
    )


def load_authority_policy_profile(path: Path) -> AuthorityPolicyProfile:
    """Load a sealed profile and reject stale identity or ambiguous YAML."""

    profile = AuthorityPolicyProfile.model_validate(_load_mapping(path))
    if (
        profile.profile_hash is None
        or profile.profile_hash != authority_policy_profile_identity(profile)
    ):
        raise ValueError("authority policy profile must be sealed and untampered")
    if profile.origin == "builtin":
        builtin = {item.profile_id: item for item in builtin_authority_profiles()}
        expected = builtin.get(profile.profile_id)
        if expected is None or expected.profile_hash != profile.profile_hash:
            raise ValueError("persisted builtin authority profile does not match builtin material")
    return profile


def load_authority_policy_profile_draft(path: Path) -> AuthorityPolicyProfile:
    """Load editable profile material while deliberately discarding any old identity."""

    value = dict(_load_mapping(path))
    value.pop("profile_hash", None)
    return AuthorityPolicyProfile.model_validate(value)


def save_authority_policy_profile(
    profile: AuthorityPolicyProfile,
    path: Path,
    *,
    overwrite: bool = False,
) -> None:
    """Atomically persist one sealed profile in deterministic JSON or YAML."""

    if (
        profile.profile_hash is None
        or profile.profile_hash != authority_policy_profile_identity(profile)
    ):
        raise ValueError("authority policy profile must be sealed and untampered")
    suffix = path.suffix.lower()
    if suffix not in PROFILE_SUFFIXES:
        raise ValueError("authority profile path must end in .json, .yaml, or .yml")
    if path.exists() and not overwrite:
        raise FileExistsError(f"authority profile already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    value = profile.model_dump(mode="json")
    if suffix == ".json":
        payload = stable_json_bytes(value) + b"\n"
    else:
        payload = yaml.safe_dump(
            value,
            allow_unicode=True,
            sort_keys=False,
        ).encode("utf-8")
    _atomic_write(path, payload, overwrite=overwrite)


def seal_authority_policy_profile_file(
    source: Path,
    output: Path,
    *,
    declared_by_actor_id: str,
    declaration_reason: str,
    overwrite: bool = False,
) -> AuthorityPolicyProfile:
    draft = load_authority_policy_profile_draft(source)
    profile = seal_authority_policy_profile(
        AuthorityPolicyProfile.model_validate(
            {
                **draft.model_dump(mode="json", exclude={"profile_hash"}),
                "origin": "project_local",
                "declared_by_actor_id": declared_by_actor_id,
                "declaration_reason": declaration_reason,
            }
        )
    )
    save_authority_policy_profile(profile, output, overwrite=overwrite)
    return profile


def resolve_authority_policy_profile(reference: str) -> AuthorityPolicyProfile:
    """Resolve a built-in ID (`builtin:` optional) or a local profile path."""

    requested = reference.removeprefix("builtin:")
    builtin = {item.profile_id: item for item in builtin_authority_profiles()}
    if requested in builtin:
        return builtin[requested]
    if reference.startswith("builtin:"):
        raise ValueError(f"unknown builtin authority profile: {requested}")
    return load_authority_policy_profile(Path(reference))


def _load_mapping(path: Path) -> Mapping[str, object]:
    suffix = path.suffix.lower()
    if suffix not in PROFILE_SUFFIXES:
        raise ValueError("authority profile path must end in .json, .yaml, or .yml")
    with path.open("rb") as handle:
        payload = handle.read(MAX_PROFILE_BYTES + 1)
    if len(payload) > MAX_PROFILE_BYTES:
        raise ValueError(f"authority profile exceeds {MAX_PROFILE_BYTES} bytes")
    text = payload.decode("utf-8-sig")
    if suffix == ".json":
        value = json.loads(text, object_pairs_hook=_unique_json_object)
    else:
        _reject_duplicate_yaml_keys(text)
        value = yaml.safe_load(text)
    if not isinstance(value, Mapping):
        raise ValueError("authority profile document must be a mapping")
    stable_json_bytes(value)
    return value


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_duplicate_yaml_keys(text: str) -> None:
    root = yaml.compose(text, Loader=yaml.SafeLoader)
    if root is None:
        return
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(node: yaml.Node, *, depth: int) -> None:
        node_id = id(node)
        if node_id in visiting:
            raise ValueError("authority profile YAML aliases must not form cycles")
        if node_id in visited:
            return
        if depth > 32:
            raise ValueError("authority profile YAML nesting exceeds 32")
        visiting.add(node_id)
        if isinstance(node, yaml.MappingNode):
            seen: set[tuple[str, str]] = set()
            for key_node, value_node in node.value:
                if not isinstance(key_node, yaml.ScalarNode):
                    raise ValueError("authority profile YAML keys must be scalar values")
                key = (key_node.tag, key_node.value)
                if key in seen:
                    raise ValueError(f"duplicate YAML key: {key_node.value!r}")
                seen.add(key)
                visit(value_node, depth=depth + 1)
        elif isinstance(node, yaml.SequenceNode):
            for item in node.value:
                visit(item, depth=depth + 1)
        visiting.remove(node_id)
        visited.add(node_id)

    visit(root, depth=0)


def _atomic_write(path: Path, payload: bytes, *, overwrite: bool) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
            temporary.unlink()
    finally:
        temporary.unlink(missing_ok=True)
