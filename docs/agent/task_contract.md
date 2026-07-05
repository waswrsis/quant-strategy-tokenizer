# Agent Task Contract

## Required Input

A substantial task should identify:

```text
Goal:
Owned paths:
Required evidence:
Allowed actions:
Forbidden actions:
Acceptance commands:
Expected artifacts:
Commit/push policy:
```

If these fields are not supplied, derive them from repository evidence and state the
assumptions before broad edits. Do not infer permission to commit, push, tag, publish,
approve, activate, or execute external/custom code.

## Required Output

Report:

- behavior and scope implemented;
- files or modules changed;
- tests and commands actually run;
- canonical identities, hashes, sentinels, or schemas intentionally changed;
- authority mode and approval state when relevant;
- boundaries preserved;
- residual risks and commands not run; and
- local commit, remote push, tag, and release status.

Acceptance requires command evidence. Intent, file existence, an agent assertion, or an
unverified remote rendering is not acceptance evidence.
