"""Deterministic vocabulary snapshots for token resolution."""

from __future__ import annotations

from qst.resolver.identity import resolver_hash
from qst.resolver.models import ResolverTokenRecord, VocabularySnapshot
from qst.tokens import TokenRegistryV2


def vocabulary_snapshot(registry: TokenRegistryV2) -> VocabularySnapshot:
    """Build a stable resolver snapshot from the accepted registry view."""

    records = tuple(
        sorted(
            (
                ResolverTokenRecord(
                    token_id=record.spec.token_id,
                    namespace=record.spec.token_ref.namespace,
                    name=record.spec.token_ref.name,
                    version=record.spec.version,
                    behavior_version=record.spec.behavior_version,
                    token_spec_hash=record.token_spec_hash,
                    inputs={name: spec.type for name, spec in record.spec.inputs.items()},
                    outputs={name: spec.type for name, spec in record.spec.outputs.items()},
                    params_schema=record.spec.params_schema,
                    maturity=record.spec.surface.maturity,
                    supported_profiles=record.spec.surface.contract.supported_profiles,
                    reserved_only=record.spec.surface.capabilities.reserved_only,
                )
                for record in registry.records
            ),
            key=lambda item: (
                item.namespace,
                item.name,
                item.version,
                item.behavior_version,
                item.token_spec_hash,
            ),
        )
    )
    material = [record.model_dump(mode="json") for record in records]
    return VocabularySnapshot(
        records=records,
        snapshot_hash=resolver_hash("qst:vocabulary-snapshot:v1", material),
    )

