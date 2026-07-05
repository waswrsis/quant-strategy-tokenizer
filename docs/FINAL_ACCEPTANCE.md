# Final Acceptance

## Candidate

This document covers the QST `1.0.0a2` research-branch candidate. Its branch/tag
publication does not constitute a production release, merge into `main`, or upstream
AI4Finance acceptance.

## Required Evidence

- Ordered rearchitecture stage manifests and local freeze evidence validate.
- Full pytest and coverage gates pass.
- Ruff, mypy, compileall, stateless lint, vocabulary, prompt, and coverage gates pass.
- v0.4 reference strategy hashes remain unchanged.
- The primary CLI exposes no custom execution command.
- `qst compat-v04 token execute` is explicitly marked legacy.
- Tampered identities, undeclared customization, invalid proposal transitions, and
  insufficient claim evidence are rejected.
- AI4Finance maturity and golden workflow tests pass.
- Strategy, experiment, and agent receipt 2.0 identity tests pass.
- FinRobot read-only diagnostics, canonical delivery, report review, and JSONL tamper tests
  pass.

## Local Result

- Full test suite passed locally.
- The `--cov-fail-under=85` package coverage gate passed locally.
- Static, prompt, artifact, coverage-frontier, vocabulary, compatibility, and stage
  manifest gates passed.
- Completion evidence is recorded in
  `docs/rearchitecture/COMPLETION_AUDIT.md`,
  `docs/rearchitecture/FULL_AUDIT.md`, and
  `docs/rearchitecture/FINROBOT_POSTS_ACCEPTANCE.md`.

## Boundary

The candidate is an evidence and governance system. It makes no claim of model training,
inference, backtesting, profitability, broker/exchange integration, HFT, order routing,
or production execution support.

The research branch is versioned by `v1.0.0a2-agent-provenance`. Promotion to `main`, a
GitHub release, or an upstream integration requires separate approval and evidence.
