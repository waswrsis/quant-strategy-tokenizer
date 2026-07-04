# Authority Policy Profiles

Stage 10 turns the Stage 9 authority modes into deterministic use-case profiles. Stage
11 updates persisted profiles to `qst-authority-policy-profile/1.1` so custom policy is
explicitly declared. A
profile is a sealed record that defines every supported use case exactly once. The
selected effective mode is returned as an identity-bearing `AuthorityModeSelection`.

## Use Cases

- `record_ingestion`
- `migration_import`
- `claim_evaluation`
- `token_review`
- `token_publication`
- `token_activation`
- `customization`

## Built-in Profiles

| Use case | record-capture | research-advisory | controlled-release | strict-governance |
|---|---|---|---|---|
| record ingestion | record only | record only | record only | enforce |
| migration import | record only | record only | record only | enforce |
| claim evaluation | record only | advisory | advisory | enforce |
| token review | record only | advisory | advisory | enforce |
| token publication | record only | enforce | enforce | enforce |
| token activation | record only | enforce | enforce | enforce |
| customization | record only | advisory | enforce | enforce |

`record-capture` remains the default to preserve QST's record-layer behavior. A caller
that wants deployment policy should select a named profile explicitly.

## Declared Overrides

An override is permitted because project context can differ from the built-in profiles.
If the effective mode differs from the configured mode, the caller must supply a
non-empty reason. The profile hash, use case, configured mode, effective mode, and
reason are sealed into the selection record.

```python
selection = select_authority_mode(
    "token_review",
    profile=research_advisory_profile(),
    mode_override="enforce",
    override_reason="This review controls a release candidate.",
)
```

The mode-aware claim, proposal-transition, and customization facades accept
`authority_profile`. Their returned records include both `mode` and `mode_selection`,
and model validation requires those values to agree.

## Boundaries

- Profiles configure record progression; they do not alter signature truth.
- Profiles do not approve actors, create grants, or sign registries.
- Structural corruption remains an error in every profile.
- Selecting a strict profile does not turn QST into an execution or trading runtime.
- Custom profiles must be complete, sealed, versioned, and evidence-bearing.
- Persisted project-local profiles must declare an actor and rationale; persisted
  builtin profiles must exactly match built-in material.

See [Authority Profile Persistence and CLI](AUTHORITY_PROFILE_CLI.md) for local file and
command usage.
