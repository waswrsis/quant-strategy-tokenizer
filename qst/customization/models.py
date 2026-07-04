"""Declared, identity-bearing semantic customizations."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import identity_hash, model_identity
from qst.provenance import normalize_utc


class CustomizationOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(pattern=r"^/(?:[^/~]|~0|~1)+(?:/(?:[^/~]|~0|~1)+)*$")
    value: Any

    @field_validator("value", mode="after")
    @classmethod
    def _json_value(cls, value: Any) -> Any:
        stable_json_bytes(value)
        return value


class CustomizationDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-customization/1.0"] = "qst-customization/1.0"
    customization_id: HashString | None = None
    requested_by_actor_id: HashString
    authored_by_actor_id: HashString
    scope: str
    rationale: str
    base_identity: HashString
    operations: tuple[CustomizationOperation, ...]
    identity_impact: Literal["none", "derived_identity_changes", "base_identity_forbidden"]
    risk: Literal["low", "medium", "high"]
    approval_required: bool
    declared_at: datetime

    @field_validator("declared_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_declaration(self) -> CustomizationDeclaration:
        if not self.operations:
            raise ValueError("customization requires operations")
        paths = [item.path for item in self.operations]
        if len(paths) != len(set(paths)):
            raise ValueError("customization operation paths must be unique")
        overlap = _first_path_overlap(paths)
        if overlap is not None:
            raise ValueError(
                f"overlapping customization paths are not allowed: {overlap[0]}, {overlap[1]}"
            )
        if self.identity_impact == "none" and self.risk != "low":
            raise ValueError("non-low-risk customization must declare identity impact")
        if self.customization_id is not None and self.customization_id != customization_identity(self):
            raise ValueError("customization_id does not match declaration material")
        return self


class CustomizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    base_identity: HashString
    customization_ids: tuple[HashString, ...]
    approval_ids: tuple[HashString, ...]
    result_identity: HashString
    value: dict[str, Any]


def customization_identity(value: CustomizationDeclaration) -> str:
    return model_identity(
        value, domain="qst:customization:v1", identity_field="customization_id"
    )


def seal_customization(value: CustomizationDeclaration) -> CustomizationDeclaration:
    return CustomizationDeclaration.model_validate(
        {
            **value.model_dump(mode="json", exclude={"customization_id"}),
            "customization_id": customization_identity(value),
        }
    )


def apply_customizations(
    base: dict[str, Any],
    declarations: tuple[CustomizationDeclaration, ...],
    *,
    approvals: dict[str, HashString] | None = None,
) -> CustomizationResult:
    """Apply sealed overlays to a copy; never mutate base material."""

    stable_json_bytes(base)
    base_identity = identity_hash("qst:customization-base:v1", base)
    result = copy.deepcopy(base)
    approvals = {} if approvals is None else approvals
    ordered = sorted(declarations, key=lambda item: item.customization_id or "")
    ids = [item.customization_id for item in ordered]
    if any(item is None for item in ids):
        raise ValueError("customization declaration must be sealed")
    if len(ids) != len(set(ids)):
        raise ValueError("customization declarations must be unique")
    all_paths = [operation.path for declaration in ordered for operation in declaration.operations]
    overlap = _first_path_overlap(all_paths)
    if overlap is not None:
        raise ValueError(
            f"overlapping customization paths are not allowed: {overlap[0]}, {overlap[1]}"
        )
    for declaration in ordered:
        if declaration.customization_id is None:
            raise ValueError("customization declaration must be sealed")
        if declaration.customization_id != customization_identity(declaration):
            raise ValueError("customization_id does not match declaration material")
        if declaration.base_identity != base_identity:
            raise ValueError("customization base_identity mismatch")
        if declaration.approval_required and declaration.customization_id not in approvals:
            raise ValueError("customization requires explicit approval")
        if declaration.identity_impact == "base_identity_forbidden":
            raise ValueError("customization declares forbidden base identity mutation")
        for operation in sorted(declaration.operations, key=lambda item: item.path):
            _set_pointer(result, operation.path, operation.value)
    customization_ids = tuple(
        item.customization_id for item in ordered if item.customization_id is not None
    )
    approval_ids = tuple(
        sorted(approvals[item] for item in customization_ids if item in approvals)
    )
    result_identity = identity_hash(
        "qst:customized-result:v1",
        {
            "base_identity": base_identity,
            "customization_ids": list(customization_ids),
            "approval_ids": list(approval_ids),
            "value": result,
        },
    )
    return CustomizationResult(
        base_identity=base_identity,
        customization_ids=customization_ids,
        approval_ids=approval_ids,
        result_identity=result_identity,
        value=result,
    )


def verify_declared_customization(
    base: dict[str, Any],
    candidate: dict[str, Any],
    declarations: tuple[CustomizationDeclaration, ...],
    *,
    approvals: dict[str, HashString] | None = None,
) -> CustomizationResult:
    """Reject a candidate containing changes not produced by declared overlays."""

    expected = apply_customizations(base, declarations, approvals=approvals)
    if stable_json_bytes(candidate) != stable_json_bytes(expected.value):
        raise ValueError("candidate contains undeclared customization")
    return expected


def _set_pointer(target: dict[str, Any], path: str, value: Any) -> None:
    parts = [item.replace("~1", "/").replace("~0", "~") for item in path[1:].split("/")]
    current: dict[str, Any] = target
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            raise ValueError(f"customization parent path does not exist: {path}")
        current = child
    current[parts[-1]] = copy.deepcopy(value)


def _first_path_overlap(paths: list[str]) -> tuple[str, str] | None:
    ordered = sorted(paths)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if right == left or right.startswith(left + "/"):
                return left, right
    return None
