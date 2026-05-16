# Strategy Authoring

prompt_system_version: qst-stage-3c-v0.3.2.1
profile_type: load_profile

## Use When

Use this profile when the user request matches strategy authoring work and the agent
needs a bounded evidence set before acting.

## Load Order

- `core/00_FOUNDATION.md`
- `readers/READ_TOKEN_SYSTEM.md`
- `readers/READ_VALIDATION_DIAGNOSTICS.md`
- `readers/READ_EXAMPLES_STRATEGIES.md`
- `tasks/CLASSIFY_STRATEGY_INTENT.md`
- `tasks/SELECT_TOKENS.md`
- `tasks/AUTHOR_GKR_STRATEGY.md`

## Stop Conditions

Stop loading once the needed repository evidence is gathered. Do not expand into unrelated
readers just because they exist, and do not carry stale facts from an earlier task.

## Output

Return the loaded readers, the reason each was loaded, and the unresolved evidence gaps.
If the task changes scope, choose a new load profile before continuing.

## Guardrails

- Use current repository evidence before making current-state claims.
- Do not invent token refs, schema fields, capabilities, or runtime behavior.
- Keep reserved design features non-executable and route unsupported behavior explicitly.
- Treat validation, hash stability, and prompt success as engineering evidence only.
