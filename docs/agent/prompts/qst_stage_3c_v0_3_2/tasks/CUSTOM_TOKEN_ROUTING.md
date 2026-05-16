# Custom Token Routing

prompt_system_version: qst-stage-3c-v0.3.2.1
task_type: security
foundation: core/00_FOUNDATION.md

## Use When

Use for any request involving custom Python entry points or external code.

## Inputs

- User request and any attached strategy, diagnostic, report, or code context.
- Repository evidence loaded through the smallest relevant reader or load profile.
- Target profile when validation, execution support, or reserved-design status matters.

## Procedure

1. Restate the task in QST terms and identify the active profile or artifact.
2. Read the current repository evidence before making token, schema, or runtime claims.
3. Apply the relevant token surface, profile gate, security, and hash boundaries.
4. Make the smallest safe change or produce the requested review.
5. Run focused validation and report any skipped gates.

Boundary words: verify, approve, execute, and must not execute code during verification.

## Output

Return verify, approve, execute, grant, and audit status separately.

## Guardrails

- Use current repository evidence before making current-state claims.
- Do not invent token refs, schema fields, capabilities, or runtime behavior.
- Keep reserved design features non-executable and route unsupported behavior explicitly.
- Treat validation, hash stability, and prompt success as engineering evidence only.
