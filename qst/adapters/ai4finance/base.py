"""Read-only declared-manifest adapter used by AI4Finance integrations."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import yaml

from qst.adapters.ai4finance.models import AdapterDescriptor, DeclaredWorkflowManifest
from qst.canonical_json import stable_json_bytes
from qst.evidence import EvidenceEnvelope, ExternalRecordEvidencePayload, evidence_identity
from qst.provenance import ArtifactDescriptor
from qst.storage import ContentAddressedStore


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key)
            if normalized_key in result:
                raise ValueError(f"workflow manifest key collision: {normalized_key}")
            result[normalized_key] = _normalize(item)
        return result
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


class DeclaredManifestAdapter:
    """Collect declared workflow evidence without importing the source project."""

    descriptor: AdapterDescriptor
    required_plan_fields: frozenset[str] = frozenset()
    required_result_fields: frozenset[str] = frozenset()

    def __init__(self, store: ContentAddressedStore) -> None:
        self.store = store

    def probe(self, source: str) -> dict[str, Any]:
        try:
            manifest = self._load(source)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            return {"ok": False, "adapter_id": self.descriptor.adapter_id, "error": str(exc)}
        return {
            "ok": manifest.system == self.descriptor.system,
            "adapter_id": self.descriptor.adapter_id,
            "system": manifest.system,
            "maturity": self.descriptor.maturity,
            "workflow_claim_eligible": self.descriptor.workflow_claim_eligible,
        }

    def discover(self, source: str) -> dict[str, Any]:
        manifest = self._load(source)
        self._validate_system(manifest)
        return {
            "run_id": manifest.run_id,
            "status": manifest.status,
            "artifact_count": len(manifest.artifacts),
        }

    def extract_plan(self, source: str) -> dict[str, Any]:
        manifest = self._load(source)
        self._validate_system(manifest)
        self._require_fields(manifest.plan, self.required_plan_fields, section="plan")
        return dict(sorted(manifest.plan.items()))

    def collect_run(self, run_ref: str) -> dict[str, Any]:
        manifest = self._load(run_ref)
        self._validate_system(manifest)
        if manifest.status == "complete":
            self._require_fields(manifest.result, self.required_result_fields, section="result")
        return {
            "run_id": manifest.run_id,
            "status": manifest.status,
            "result": dict(sorted(manifest.result.items())),
        }

    def describe_artifacts(self, run_ref: str) -> tuple[ArtifactDescriptor, ...]:
        manifest_path = Path(run_ref).resolve(strict=True)
        manifest = self._load(str(manifest_path))
        self._validate_system(manifest)
        descriptors: list[ArtifactDescriptor] = []
        for artifact in sorted(manifest.artifacts, key=lambda item: (item.role, item.path)):
            path = (manifest_path.parent / artifact.path).resolve(strict=True)
            if not path.is_relative_to(manifest_path.parent):
                raise ValueError("artifact path escapes manifest directory")
            descriptors.append(self.store.put_file(path, media_type=artifact.media_type))
        return tuple(descriptors)

    def verify(self, evidence: EvidenceEnvelope) -> bool:
        payload = evidence.payload
        if not (
            isinstance(payload, ExternalRecordEvidencePayload)
            and payload.adapter_id == self.descriptor.adapter_id
            and payload.record_schema == "qst-ai4finance-workflow/1.0"
            and evidence.evidence_id is not None
            and evidence.evidence_id == evidence_identity(evidence)
        ):
            return False
        run_id = payload.record.get("run_id")
        status = payload.record.get("status")
        result = payload.record.get("result")
        if not isinstance(run_id, str) or not run_id or evidence.subject_ref != run_id:
            return False
        if status not in {"planned", "running", "partial", "complete", "failed"}:
            return False
        if not isinstance(result, dict):
            return False
        if status == "complete" and not self.required_result_fields <= set(result):
            return False
        return True

    def _load(self, source: str) -> DeclaredWorkflowManifest:
        raw = yaml.safe_load(Path(source).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("workflow manifest must be a mapping")
        normalized = _normalize(cast(dict[str, Any], raw))
        stable_json_bytes(normalized)
        return DeclaredWorkflowManifest.model_validate(normalized)

    def _validate_system(self, manifest: DeclaredWorkflowManifest) -> None:
        if manifest.system != self.descriptor.system:
            raise ValueError(
                f"adapter {self.descriptor.adapter_id} cannot read system {manifest.system}"
            )

    @staticmethod
    def _require_fields(value: dict[str, Any], required: frozenset[str], *, section: str) -> None:
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(f"{section} missing required fields: {', '.join(missing)}")
