# P1-Extended-A Validators

## Scope

- purity validator
- temporal safety validator
- profile-aware warnings and failures

## Non-Scope

- recipe-level temporal aggregation
- provenance tag
- TagSpec
- recipe generator
- CSE
- kernel substitution
- complex recipe validation
- FSM
- expanded indicator library

## Profile Rules

| Profile | Max purity | Future data | Unsafe window modes |
|---|---|---|---|
| `research` | external_read | warning | warning |
| `paper` | external_read | warning | warning |
| `pretrade` | contextual_read | error | error |
| `production_guarded` | contextual_read | error | error |

`external_write` is rejected for every profile.

Unsafe strict window modes:

- `centered`
- `full_sample`
- `mixed`
- `unknown`

## Repair Hints

Purity violations use:

```json
{
  "kind": "replace_token_or_change_profile",
  "options": [
    {"op": "ChangeProfile", "to": "research"},
    {"op": "ReplaceToken", "reason": "use contextual_read equivalent"}
  ]
}
```

Future-data violations use:

```json
{
  "kind": "replace_token",
  "suggestion": "use trailing-window variant"
}
```

Unsafe temporal windows use:

```json
{
  "kind": "replace_token_or_change_profile",
  "suggestion": "use trailing window or research profile"
}
```

## Acceptance Commands

```bash
python -m pytest tests/ir/test_purity_validator.py -v
python -m pytest tests/ir/test_temporal_validator.py -v
python -m pytest tests/e2e/test_p1_extended_a_validators.py -v
python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v
```
