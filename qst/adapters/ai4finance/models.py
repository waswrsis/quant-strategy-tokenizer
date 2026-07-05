"""Shared models for declared AI4Finance evidence workflows."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AdapterMaturity = Literal["L0", "L1", "L2", "L3", "L4"]
WorkflowSystem = Literal["finrobot", "fingpt", "finrl_meta", "finrl", "finrl_x", "qlib"]


class AdapterDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_id: str
    system: WorkflowSystem
    maturity: AdapterMaturity
    adapter_version: str = "1.0.0a2"
    evidence_only: bool = True

    @property
    def workflow_claim_eligible(self) -> bool:
        return self.maturity in {"L3", "L4"}


class DeclaredArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    media_type: str
    role: str


class DeclaredWorkflowManifest(BaseModel):
    """Project wrapper manifest; it points at outputs but never launches a run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-ai4finance-workflow/1.0"] = "qst-ai4finance-workflow/1.0"
    system: WorkflowSystem
    run_id: str
    status: Literal["planned", "running", "partial", "complete", "failed"]
    plan: dict[str, Any]
    result: dict[str, Any] = Field(default_factory=dict)
    artifacts: tuple[DeclaredArtifact, ...] = ()

    @model_validator(mode="after")
    def _complete_has_artifacts(self) -> DeclaredWorkflowManifest:
        if self.status == "complete" and not self.artifacts:
            raise ValueError("complete workflow manifest requires artifacts")
        return self
