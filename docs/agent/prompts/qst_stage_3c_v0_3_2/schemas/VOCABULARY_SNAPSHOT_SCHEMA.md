# Vocabulary Snapshot Schema

prompt_system_version: qst-stage-3c-v0.3.2.1
schema_type: prompt_contract

## Purpose

Define a compact token vocabulary snapshot for agent reasoning.

## Required Fields

- token_ref, family, maturity, execution_support, contract_scope, capabilities, profile_caveats

## Validation Rules

- values must come from current built-in packs, not memory.
- Missing fields must be reported explicitly instead of inferred.
- Output should be deterministic and compact enough for review.

## Output

Return a mapping or report that follows the required field list and preserves unresolved
questions for the next agent.

## Guardrails

- Use current repository evidence before making current-state claims.
- Do not invent token refs, schema fields, capabilities, or runtime behavior.
- Keep reserved design features non-executable and route unsupported behavior explicitly.
- Treat validation, hash stability, and prompt success as engineering evidence only.
