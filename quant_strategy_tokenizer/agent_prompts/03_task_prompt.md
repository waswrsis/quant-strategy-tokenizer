# Generic Task Prompt

```text
Task:
[Describe the requested change or audit here.]

Repository/context:
[Describe local path, strategy file, deployment targets, known public/private differences, and relevant recent incidents.]

Required behavior:
- Preserve current live defaults unless explicitly changed.
- Do not modify remote systems unless explicitly instructed.
- Do not restart live processes unless explicitly instructed.
- Treat risk-control behavior as production-critical.
- Keep public/private parameters separate.
- Prefer explicit failure states over silent fallback.

Work process:
1. Inspect the relevant code and README/config first.
2. Identify the current behavior and the intended behavior.
3. Implement the smallest safe change.
4. Run compile/smoke/regression checks.
5. Audit the changed paths for similar failure modes.
6. Report changed files, verification results, and remaining risks.

Output format:
- Summary
- Files changed
- Behavior preserved
- Behavior changed
- Verification
- Residual risk
```

