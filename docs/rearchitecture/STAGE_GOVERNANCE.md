# Stage Governance

## Freeze Unit

Every stage is closed by all three artifacts:

1. a checked-in manifest under `docs/rearchitecture/stages/`;
2. a local Git commit containing the accepted stage changes;
3. an annotated local tag named `qst-1.0-stage-N-<slug>-frozen`.

The tag is the authoritative immutable snapshot. The manifest records scope, frozen
contracts, gates, and evidence without embedding a self-referential commit hash.

## Gate Rule

A stage may be marked `frozen` only when every required gate has result `pass`. The next
stage must not start while the preceding manifest is `planned`, `active`, `failed`, or
`candidate`.

Use:

```bash
python tools/validate_rearchitecture_stages.py
python tools/validate_rearchitecture_stages.py --check-git-tags
```

The first command is used before the stage commit. The tag-aware command is run after
the local commit and annotated tag are created.

## Supersession Rule

Frozen Git history is never rewritten. If later work must change a frozen public
contract, the later stage must:

1. name the superseded stage and contract;
2. provide a reason and migration effect;
3. add focused regression tests for old and new behavior;
4. record the supersession in its own manifest.

Ordinary implementation files may evolve when a later stage explicitly owns them.
Frozen contract definitions, diagnostic codes, schemas, and identity material may not
change implicitly.

## Git and Publication Rule

- Work occurs on `research/qst-1.0-agent-provenance`.
- Stage commits and freeze tags remain local.
- No force push, GitHub push, pull request, release, or remote tag is allowed without
  explicit user approval.

