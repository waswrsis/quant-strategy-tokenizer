"""Strategy, experiment, and agent receipt identity layers."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash import compute_hashes_v2
from qst.hash.common import HashString
from qst.identity import identity_hash, model_identity
from qst.ir import StrategyIRV04, canonical_bytes_v04, validate_ir_v04


class StrategyRecordReceipt(BaseModel):
    """Identity and validation record for a complete canonical GKR document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-strategy-record-receipt/2.0"] = (
        "qst-strategy-record-receipt/2.0"
    )
    strategy_receipt_id: HashString | None = None
    strategy_hash: HashString
    graph_hash: HashString
    param_hash: HashString
    instance_hash: HashString
    canonical_digest: HashString
    canonical_size: int = Field(ge=1)
    validation_ok: bool
    diagnostic_codes: tuple[str, ...] = ()
    non_goals: tuple[str, ...] = Field(min_length=1)

    @field_validator("diagnostic_codes", "non_goals", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @model_validator(mode="after")
    def _identity(self) -> StrategyRecordReceipt:
        if (
            self.strategy_receipt_id is not None
            and self.strategy_receipt_id != strategy_receipt_identity(self)
        ):
            raise ValueError("strategy_receipt_id does not match receipt material")
        return self


class EvaluationWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: date
    end: date

    @model_validator(mode="after")
    def _ordered(self) -> EvaluationWindow:
        if self.end < self.start:
            raise ValueError("evaluation window end cannot precede start")
        return self


class ExperimentReceipt(BaseModel):
    """Strict record of externally executed experiment identity material."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-experiment-receipt/2.0"] = "qst-experiment-receipt/2.0"
    experiment_hash: HashString | None = None
    subject_ref: str = Field(min_length=1)
    strategy_receipt_id: HashString
    strategy_hash: HashString
    data_snapshot_ids: tuple[HashString, ...] = Field(min_length=1)
    evaluation_window: EvaluationWindow
    evaluator_adapter_id: str = Field(min_length=1)
    evaluator_adapter_version: str = Field(min_length=1)
    parameters: dict[str, Any]
    costs: dict[str, Any]
    slippage: dict[str, Any]
    seeds: tuple[int, ...] = Field(min_length=1)
    metric_definitions: dict[str, str]
    result_evidence_ids: tuple[HashString, ...] = Field(min_length=1)

    @field_validator("data_snapshot_ids", "result_evidence_ids", mode="after")
    @classmethod
    def _sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("seeds", mode="after")
    @classmethod
    def _sort_seeds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("parameters", "costs", "slippage", mode="after")
    @classmethod
    def _json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return dict(sorted(value.items()))

    @field_validator("costs", "slippage", "metric_definitions", mode="after")
    @classmethod
    def _nonempty_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("experiment costs, slippage, and metric definitions must be explicit")
        return value

    @field_validator("metric_definitions", mode="after")
    @classmethod
    def _metric_definitions(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not key.strip() or not description.strip() for key, description in value.items()):
            raise ValueError("metric definitions require non-empty names and descriptions")
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def _identity(self) -> ExperimentReceipt:
        if self.experiment_hash is not None and self.experiment_hash != experiment_identity(self):
            raise ValueError("experiment_hash does not match receipt material")
        return self


class AgentReceipt(BaseModel):
    """Agent recommendation identity bound to an experiment and produced artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-agent-receipt/2.0"] = "qst-agent-receipt/2.0"
    agent_receipt_hash: HashString | None = None
    experiment_hash: HashString
    agent_actor_id: HashString
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    tool_versions: dict[str, str]
    prompt_ref: str = Field(min_length=1)
    task_ref: str = Field(min_length=1)
    approval_ids: tuple[HashString, ...] = ()
    output_artifact_ids: tuple[HashString, ...] = Field(min_length=1)
    recommendation: dict[str, Any]

    @field_validator("approval_ids", "output_artifact_ids", mode="after")
    @classmethod
    def _sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("tool_versions", "recommendation", mode="after")
    @classmethod
    def _json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return dict(sorted(value.items()))

    @field_validator("tool_versions", "recommendation", mode="after")
    @classmethod
    def _nonempty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("agent tool versions and recommendation must be explicit")
        return value

    @model_validator(mode="after")
    def _identity(self) -> AgentReceipt:
        if self.agent_receipt_hash is not None and self.agent_receipt_hash != agent_identity(self):
            raise ValueError("agent_receipt_hash does not match receipt material")
        return self


def canonical_strategy_identity(ir: StrategyIRV04) -> str:
    """Hash the complete canonical GKR in a receipt-specific domain."""

    canonical = json.loads(canonical_bytes_v04(ir).decode("utf-8"))
    return identity_hash("qst:canonical-strategy:v2", {"canonical_gkr": canonical})


def strategy_receipt_identity(value: StrategyRecordReceipt) -> str:
    return model_identity(
        value, domain="qst:strategy-record-receipt:v2", identity_field="strategy_receipt_id"
    )


def experiment_identity(value: ExperimentReceipt) -> str:
    return model_identity(
        value, domain="qst:experiment-receipt:v2", identity_field="experiment_hash"
    )


def agent_identity(value: AgentReceipt) -> str:
    return model_identity(
        value, domain="qst:agent-receipt:v2", identity_field="agent_receipt_hash"
    )


def build_strategy_record_receipt(
    ir: StrategyIRV04, *, non_goals: tuple[str, ...]
) -> StrategyRecordReceipt:
    """Build and seal a strategy receipt from current canonical and validation APIs."""

    canonical = canonical_bytes_v04(ir)
    hashes = compute_hashes_v2(ir)
    validation = validate_ir_v04(ir)
    value = StrategyRecordReceipt(
        strategy_hash=canonical_strategy_identity(ir),
        graph_hash=hashes.graph_hash,
        param_hash=hashes.param_hash,
        instance_hash=hashes.instance_hash,
        canonical_digest=f"sha256:{hashlib.sha256(canonical).hexdigest()}",
        canonical_size=len(canonical),
        validation_ok=validation.ok,
        diagnostic_codes=tuple(item.code for item in validation.diagnostics),
        non_goals=non_goals,
    )
    return seal_strategy_record_receipt(value)


def seal_strategy_record_receipt(value: StrategyRecordReceipt) -> StrategyRecordReceipt:
    return StrategyRecordReceipt.model_validate(
        {
            **value.model_dump(mode="json", exclude={"strategy_receipt_id"}),
            "strategy_receipt_id": strategy_receipt_identity(value),
        }
    )


def seal_experiment_receipt(value: ExperimentReceipt) -> ExperimentReceipt:
    return ExperimentReceipt.model_validate(
        {
            **value.model_dump(mode="json", exclude={"experiment_hash"}),
            "experiment_hash": experiment_identity(value),
        }
    )


def seal_agent_receipt(value: AgentReceipt) -> AgentReceipt:
    return AgentReceipt.model_validate(
        {
            **value.model_dump(mode="json", exclude={"agent_receipt_hash"}),
            "agent_receipt_hash": agent_identity(value),
        }
    )
