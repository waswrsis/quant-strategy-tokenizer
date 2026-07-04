"""Strategy, experiment, and agent receipt identity layers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity


class ExperimentReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-experiment-receipt/1.0"] = "qst-experiment-receipt/1.0"
    experiment_hash: HashString | None = None
    strategy_hash: HashString
    data_snapshot_ids: tuple[HashString, ...]
    evaluator_adapter_id: str
    evaluator_adapter_version: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    costs: dict[str, Any] = Field(default_factory=dict)
    seeds: tuple[int, ...] = ()

    @field_validator("data_snapshot_ids", mode="after")
    @classmethod
    def _sort_data(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("seeds", mode="after")
    @classmethod
    def _sort_seeds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("parameters", "costs", mode="after")
    @classmethod
    def _json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value

    @model_validator(mode="after")
    def _identity(self) -> ExperimentReceipt:
        if self.experiment_hash is not None and self.experiment_hash != experiment_identity(self):
            raise ValueError("experiment_hash does not match receipt material")
        return self


class AgentReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-agent-receipt/1.0"] = "qst-agent-receipt/1.0"
    agent_receipt_hash: HashString | None = None
    experiment_hash: HashString
    agent_actor_id: HashString
    model_id: str
    tool_versions: dict[str, str]
    prompt_ref: str
    task_ref: str
    approval_ids: tuple[HashString, ...] = ()
    recommendation: dict[str, Any]

    @field_validator("approval_ids", mode="after")
    @classmethod
    def _sort_approvals(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("tool_versions", "recommendation", mode="after")
    @classmethod
    def _json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def _identity(self) -> AgentReceipt:
        if self.agent_receipt_hash is not None and self.agent_receipt_hash != agent_identity(self):
            raise ValueError("agent_receipt_hash does not match receipt material")
        return self


def experiment_identity(value: ExperimentReceipt) -> str:
    return model_identity(
        value, domain="qst:experiment-receipt:v1", identity_field="experiment_hash"
    )


def agent_identity(value: AgentReceipt) -> str:
    return model_identity(
        value, domain="qst:agent-receipt:v1", identity_field="agent_receipt_hash"
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

