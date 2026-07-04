# Authority Profile Persistence and CLI

Stage 11 provides deterministic local persistence and a non-executing CLI for authority
policy profiles. These commands inspect, seal, validate, and select policy records. They
do not sign approvals or run governed operations.

## Built-in Profiles

```bash
python -m qst.cli authority profile list
python -m qst.cli authority profile show research-advisory
python -m qst.cli authority profile show builtin:controlled-release
```

## Export and Validate

```bash
python -m qst.cli authority profile export research-advisory \
  --output .qst/authority/research-advisory.yaml

python -m qst.cli authority profile validate \
  .qst/authority/research-advisory.yaml
```

JSON, YAML, and YML files are supported. Files are size-bounded, duplicate object keys
are rejected, YAML uses `SafeLoader`, identities are revalidated, and writes are atomic.

## Declared Project Profiles

An edited profile cannot remain a builtin. Seal it as `project_local` with a declaring
actor identity and rationale:

```bash
python -m qst.cli authority profile seal profile-draft.yaml \
  --output .qst/authority/project-release.yaml \
  --declared-by-actor-id sha256:<actor-identity> \
  --declaration-reason "Project release policy"
```

The resulting `qst-authority-policy-profile/1.1` record includes its origin,
declaration, complete use-case mapping, and profile hash. Persisted files claiming
`builtin` origin must exactly match the corresponding built-in profile hash.

## Select a Mode

```bash
python -m qst.cli authority mode select token_review \
  --profile research-advisory

python -m qst.cli authority mode select token_review \
  --profile research-advisory \
  --mode-override enforce \
  --override-reason "Release candidate review"
```

The output is a sealed `qst-authority-mode-selection/1.0` record. It is evidence of
configuration selection, not evidence that any actor or action was authorized.

## Boundaries

- No command imports private keys or signs governance statements.
- No command grants, approves, publishes, activates, or executes anything.
- Profile files are local configuration records, not a global trust registry.
- Applications remain responsible for selecting and pinning the profile they use.
