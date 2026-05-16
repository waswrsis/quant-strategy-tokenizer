# Author Gkr Strategy

prompt_system_version: qst-stage-3c-v0.3.2.2
task_type: authoring
foundation: core/00_FOUNDATION.md

## Use When

Use when creating a new editable GKR strategy source.

## Inputs

- User request and any attached strategy, diagnostic, report, or code context.
- Repository evidence loaded through the smallest relevant reader or load profile.
- Target profile when validation, execution support, or reserved-design status matters.

## Preconditions

- classification is `supported` or `partially_supported`
- `token_selection.may_author_gkr` is true
- `repo_context` exists
- at least one current example strategy has been inspected

## Procedure

1. Inspect the closest example strategy under `examples/strategies/<case>/strategy.gkr.yaml`.
2. Build a deterministic node plan.
3. Use stable node ids.
4. Use only selected token refs.
5. Use explicit params and explicit input links.
6. Add only required capabilities.
7. Write or patch the `.gkr.yaml` source.
8. Run `qst validate <strategy.gkr.yaml>`.
9. If validation passes, run `qst hash <strategy.gkr.yaml>`.
10. If validation passes, run `qst canonicalize <strategy.gkr.yaml> --output <tmp canonical path>`.
11. If validation fails, route to `tasks/REPAIR_GKR_DIAGNOSTICS.md`.

## Output

Return a node plan and final authoring evidence:

```yaml
node_plan:
  - node_id:
    token_ref:
    purpose:
    params:
    inputs:
    outputs:
    evidence:
```

```yaml
gkr_authoring:
  file:
  node_plan:
  capabilities:
  validation:
    command:
    result:
    diagnostics:
  hash:
    graph_hash:
    param_hash:
    instance_hash:
  canonical:
    output:
  repair_needed:
  limitations:
```

## Guardrails

- Use current repository evidence before making current-state claims.
- Do not invent token refs, schema fields, capabilities, or runtime behavior.
- Keep reserved design features non-executable and route unsupported behavior explicitly.
- Treat validation, hash stability, and prompt success as engineering evidence only.
- Do not author a strategy when token selection contains reserved blockers or unresolved
  custom token approval requirements.
