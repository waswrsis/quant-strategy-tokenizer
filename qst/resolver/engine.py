"""Two-phase deterministic token-gap resolver."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from qst.canonical_json import stable_json_bytes
from qst.resolver.identity import resolver_hash
from qst.resolver.models import (
    CandidateFacts,
    RecipeSpec,
    ResolutionIdentity,
    ResolutionResult,
    ResolverIssue,
    ResolverPolicy,
    ResolverRoute,
    ResolverTokenRecord,
    TokenIntent,
    TokenProposalSummary,
    VocabularySnapshot,
)
from qst.types import TypeSpec


class TokenGapResolver:
    """Collect all facts first, then evaluate the immutable v1 route lattice."""

    def __init__(
        self,
        snapshot: VocabularySnapshot,
        *,
        policy: ResolverPolicy | None = None,
        aliases: dict[str, str] | None = None,
        recipes: tuple[RecipeSpec, ...] = (),
        proposals: tuple[TokenProposalSummary, ...] = (),
        profile_policy_material: dict[str, Any] | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.policy = policy or ResolverPolicy()
        self.aliases = dict(sorted((aliases or {}).items()))
        self.recipes = tuple(sorted(recipes, key=lambda item: item.recipe_id))
        self.proposals = tuple(sorted(proposals, key=lambda item: item.proposal_id))
        self.profile_policy_material = profile_policy_material or {
            "policy": "token-contract-supported-profiles"
        }
        stable_json_bytes(self.aliases)
        stable_json_bytes(self.profile_policy_material)

    def resolve(self, value: TokenIntent | dict[str, Any]) -> ResolutionResult:
        """Resolve structured intent without fuzzy matching or short-circuit fact collection."""

        raw = value.model_dump(mode="json") if isinstance(value, TokenIntent) else value
        raw_hash = resolver_hash("qst:token-intent:v1", raw)
        try:
            intent = value if isinstance(value, TokenIntent) else TokenIntent.model_validate(value)
        except ValidationError as exc:
            issues = tuple(
                ResolverIssue(
                    code="QST_RESOLVER_INVALID_INTENT",
                    path=".".join(str(item) for item in error["loc"]),
                    message=error["msg"],
                )
                for error in exc.errors(include_url=False)
            )
            return self._result(
                route="invalid_intent",
                intent=None,
                intent_hash=raw_hash,
                candidates=(),
                issues=issues,
            )

        candidates = self._collect_candidates(intent)
        evidence_only_terms = set(self.policy.evidence_only_runtime_terms)
        non_goal_terms = tuple(
            sorted(term for term in intent.runtime_requirements if term not in evidence_only_terms)
        )
        reserved_terms = set(intent.required_types) & set(self.policy.reserved_type_terms)
        reserved_terms.update(candidate.token_id for candidate in candidates if candidate.reserved)
        boundary_terms = non_goal_terms or tuple(sorted(reserved_terms))
        recipes = self._matching_recipes(intent)
        proposals = self._matching_proposals(intent)

        compatible = tuple(
            item
            for item in candidates
            if item.status in {"exact_compatible", "alias_compatible", "version_compatible"}
            and not item.reserved
        )
        conditions: dict[ResolverRoute, bool] = {
            "invalid_intent": False,
            "non_goal_runtime": bool(non_goal_terms),
            "reserved_typespec": bool(reserved_terms),
            "direct_token_match": bool(compatible),
            "recipe_match": bool(recipes),
            "existing_proposal": bool(proposals),
            "new_token_gap": True,
        }
        route = next(route for route in self.policy.route_precedence if conditions[route])
        return self._result(
            route=route,
            intent=intent,
            intent_hash=raw_hash,
            candidates=candidates,
            boundary_terms=tuple(boundary_terms),
            matched_recipe_id=recipes[0].recipe_id if route == "recipe_match" else None,
            matched_proposal_id=proposals[0].proposal_id if route == "existing_proposal" else None,
            issues=(),
        )

    def _collect_candidates(self, intent: TokenIntent) -> tuple[CandidateFacts, ...]:
        requested = intent.requested_token_id or intent.concept
        alias_target = self.aliases.get(requested)
        candidates: list[CandidateFacts] = []
        for record in self.snapshot.records:
            identifier_match: str | None = None
            if record.token_id == requested:
                identifier_match = "exact"
            elif alias_target == record.token_id:
                identifier_match = "alias"
            if identifier_match is None:
                continue

            version_compatible = intent.version is None or (
                record.version == intent.version
                and (
                    intent.behavior_version is None
                    or record.behavior_version == intent.behavior_version
                )
            )
            if identifier_match == "exact" and not version_compatible:
                identifier_match = "version"
            ports_compatible, types_compatible, port_issues = _port_facts(intent, record)
            params_compatible, param_issues = _params_compatible(intent.params, record.params_schema)
            profile_allowed = intent.target_profile in record.supported_profiles
            reserved = record.reserved_only or record.maturity == "reserved_design"
            compatible = all(
                (
                    version_compatible,
                    ports_compatible,
                    types_compatible,
                    params_compatible,
                    profile_allowed,
                )
            )
            status = f"{identifier_match}_{'compatible' if compatible else 'incompatible'}"
            incompatibilities = [*port_issues, *param_issues]
            if not version_compatible:
                incompatibilities.append("version")
            if not profile_allowed:
                incompatibilities.append("profile")
            candidates.append(
                CandidateFacts(
                    token_id=record.token_id,
                    token_spec_hash=record.token_spec_hash,
                    namespace=record.namespace,
                    name=record.name,
                    version=record.version,
                    behavior_version=record.behavior_version,
                    status=status,  # type: ignore[arg-type]
                    identifier_match=identifier_match,  # type: ignore[arg-type]
                    version_compatible=version_compatible,
                    ports_compatible=ports_compatible,
                    types_compatible=types_compatible,
                    params_compatible=params_compatible,
                    profile_allowed=profile_allowed,
                    reserved=reserved,
                    incompatibilities=tuple(sorted(set(incompatibilities))),
                )
            )
        return tuple(
            sorted(
                candidates,
                key=lambda item: (
                    self.policy.candidate_status_rank[item.status],
                    item.namespace,
                    item.name,
                    item.version,
                    item.behavior_version,
                    item.token_spec_hash,
                ),
            )
        )

    def _matching_recipes(self, intent: TokenIntent) -> tuple[RecipeSpec, ...]:
        available = {
            f"{item.namespace}.{item.name}/v{item.version}/bv{item.behavior_version}"
            for item in self.snapshot.records
            if not item.reserved_only
            and item.maturity != "reserved_design"
            and intent.target_profile in item.supported_profiles
        }
        matches: list[RecipeSpec] = []
        for recipe in self.recipes:
            ports_compatible, types_compatible, _ = _port_map_facts(
                intent,
                recipe.inputs,
                recipe.outputs,
            )
            params_compatible, _ = _params_compatible(intent.params, recipe.params_schema)
            if (
                intent.concept in recipe.concepts
                and set(recipe.token_refs) <= available
                and intent.target_profile in recipe.supported_profiles
                and ports_compatible
                and types_compatible
                and params_compatible
            ):
                matches.append(recipe)
        return tuple(matches)

    def _matching_proposals(self, intent: TokenIntent) -> tuple[TokenProposalSummary, ...]:
        return tuple(
            proposal
            for proposal in self.proposals
            if proposal.concept == intent.concept and proposal.status != "rejected"
        )

    def _result(
        self,
        *,
        route: ResolverRoute,
        intent: TokenIntent | None,
        intent_hash: str,
        candidates: tuple[CandidateFacts, ...],
        boundary_terms: tuple[str, ...] = (),
        matched_recipe_id: str | None = None,
        matched_proposal_id: str | None = None,
        issues: tuple[ResolverIssue, ...],
    ) -> ResolutionResult:
        recipe_hash = resolver_hash(
            "qst:recipe-catalog:v1",
            [item.model_dump(mode="json") for item in self.recipes],
        )
        proposal_hash = resolver_hash(
            "qst:proposal-catalog:v1",
            [item.model_dump(mode="json") for item in self.proposals],
        )
        profile_hash = resolver_hash(
            "qst:profile-policy:v1", self.profile_policy_material
        )
        alias_hash = resolver_hash("qst:alias-catalog:v1", self.aliases)
        policy_hash = resolver_hash(
            "qst:resolver-policy:v1", self.policy.model_dump(mode="json")
        )
        decision_material = {
            "route": route,
            "intent_hash": intent_hash,
            "vocabulary_snapshot_hash": self.snapshot.snapshot_hash,
            "alias_catalog_hash": alias_hash,
            "recipe_catalog_hash": recipe_hash,
            "proposal_catalog_hash": proposal_hash,
            "profile_policy_hash": profile_hash,
            "resolver_policy_hash": policy_hash,
            "candidates": [item.model_dump(mode="json") for item in candidates],
            "matched_recipe_id": matched_recipe_id,
            "matched_proposal_id": matched_proposal_id,
            "boundary_terms": list(boundary_terms),
            "issues": [item.model_dump(mode="json") for item in issues],
        }
        identity = ResolutionIdentity(
            intent_hash=intent_hash,
            vocabulary_snapshot_hash=self.snapshot.snapshot_hash,
            alias_catalog_hash=alias_hash,
            recipe_catalog_hash=recipe_hash,
            proposal_catalog_hash=proposal_hash,
            profile_policy_hash=profile_hash,
            resolver_policy_hash=policy_hash,
            resolution_hash=resolver_hash("qst:resolver-decision:v1", decision_material),
        )
        return ResolutionResult(
            route=route,
            intent=intent,
            identity=identity,
            candidates=candidates,
            matched_recipe_id=matched_recipe_id,
            matched_proposal_id=matched_proposal_id,
            boundary_terms=boundary_terms,
            issues=issues,
        )


def _port_facts(
    intent: TokenIntent, record: ResolverTokenRecord
) -> tuple[bool, bool, tuple[str, ...]]:
    return _port_map_facts(intent, record.inputs, record.outputs)


def _port_map_facts(
    intent: TokenIntent,
    record_inputs: dict[str, TypeSpec],
    record_outputs: dict[str, TypeSpec],
) -> tuple[bool, bool, tuple[str, ...]]:
    issues: list[str] = []
    ports_compatible = True
    types_compatible = True
    for direction, requested, available in (
        ("input", intent.inputs, record_inputs),
        ("output", intent.outputs, record_outputs),
    ):
        if not requested:
            continue
        if set(requested) != set(available):
            ports_compatible = False
            issues.append(f"{direction}_ports")
        for name in sorted(set(requested) & set(available)):
            if not _same_type(requested[name], available[name]):
                types_compatible = False
                issues.append(f"{direction}_type:{name}")
    return ports_compatible, types_compatible, tuple(issues)


def _same_type(left: TypeSpec, right: TypeSpec) -> bool:
    return left.model_dump(mode="json") == right.model_dump(mode="json")


def _params_compatible(
    params: dict[str, Any], schema: dict[str, Any]
) -> tuple[bool, tuple[str, ...]]:
    issues: list[str] = []
    required = set(schema.get("required", []))
    missing = sorted(required - set(params))
    issues.extend(f"param_missing:{name}" for name in missing)
    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        unknown = sorted(set(params) - set(properties))
        issues.extend(f"param_unknown:{name}" for name in unknown)
    for name in sorted(set(params) & set(properties)):
        constraint = properties[name]
        value = params[name]
        expected = constraint.get("type")
        if expected is not None and not _json_type_matches(value, expected):
            issues.append(f"param_type:{name}")
            continue
        if "enum" in constraint and value not in constraint["enum"]:
            issues.append(f"param_enum:{name}")
        if "const" in constraint and value != constraint["const"]:
            issues.append(f"param_const:{name}")
        if isinstance(value, str) and "minLength" in constraint:
            if len(value) < constraint["minLength"]:
                issues.append(f"param_min_length:{name}")
        if isinstance(value, list) and constraint.get("uniqueItems") is True:
            encoded = [stable_json_bytes(item) for item in value]
            if len(encoded) != len(set(encoded)):
                issues.append(f"param_unique_items:{name}")
        if isinstance(value, int | float) and not isinstance(value, bool):
            if "minimum" in constraint and value < constraint["minimum"]:
                issues.append(f"param_minimum:{name}")
            if "maximum" in constraint and value > constraint["maximum"]:
                issues.append(f"param_maximum:{name}")
    return not issues, tuple(issues)


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "null":
        return value is None
    return False
