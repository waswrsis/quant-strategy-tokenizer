# Final Acceptance

## Candidate

This document covers the local QST `1.0.0a1` candidate. It does not constitute a GitHub
release or remote acceptance.

## Required Evidence

- Stage manifests 0 through 8 validate and every local freeze tag exists.
- Full pytest and coverage gates pass.
- Ruff, mypy, compileall, stateless lint, vocabulary, prompt, and coverage gates pass.
- v0.4 reference strategy hashes remain unchanged.
- The primary CLI exposes no custom execution command.
- `qst compat-v04 token execute` is explicitly marked legacy.
- Tampered identities, undeclared customization, invalid proposal transitions, and
  insufficient claim evidence are rejected.
- AI4Finance maturity and golden workflow tests pass.

## Local Result

- Full suite: `606 passed`.
- Coverage suite: `606 passed`; `89.73%` total package coverage.
- Static, prompt, artifact, coverage-frontier, vocabulary, compatibility, and stage
  manifest gates passed.
- Completion evidence is recorded in
  `docs/rearchitecture/COMPLETION_AUDIT.md`,
  `docs/rearchitecture/FULL_AUDIT.md`, and the Stage 8 manifest.

## Boundary

The candidate is an evidence and governance system. It makes no claim of model training,
inference, backtesting, profitability, broker/exchange integration, HFT, order routing,
or production execution support.

The final commit and freeze tag remain local until the user authorizes GitHub submission.
