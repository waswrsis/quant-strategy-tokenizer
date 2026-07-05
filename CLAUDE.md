# QST Project Instructions

## Product

- QST `1.0.0a2` is a deterministic record, evidence, claim, and governance layer for
  financial agents.
- `qst-ir/0.4` and `qst-canonical/0.4` remain the strategy compatibility surface.
- QST does not train models, run inference or backtests, route orders, connect to brokers
  or exchanges, publish reports, or claim profitability.

## Start Here

1. Run `git status --short`, `git branch --show-current`, and `git rev-parse HEAD`.
2. Read `README.md` and `docs/agent/QST_1_0_AGENT_PROMPT.md`.
3. For receipt, claim, or FinRobot work, read:
   - `docs/agent/RECORD_LAYER_WORKFLOW.md`
   - `docs/rearchitecture/FINROBOT_POSTS_ACCEPTANCE.md`
4. Load other documents only when the task requires them.

## Core Separations

- Evidence is not approval.
- A receipt is not an execution grant.
- Claim evaluation is not authority evaluation.
- Integrity verification is not trust approval.
- Publication and activation are separate human-governed transitions.
- Authority mode never changes whether evidence is factually sufficient.

## Editing Rules

- Preserve user changes and inspect the current implementation before editing.
- Prefer existing models, canonical helpers, diagnostics, and tests.
- Add negative-path tests for identity, admission, authority, and security changes.
- Do not weaken a gate to make a fixture pass.
- Do not add a built-in token solely to improve coverage metrics.
- Do not execute custom Python or external financial workflows unless the user explicitly
  requests it and the relevant approval/grant boundary is satisfied.

## Common Gates

```bash
python -m ruff check .
python -m mypy qst
python -m qst.lint.stateless qst
python -m pytest tests -q
python -m pytest --cov=qst --cov-fail-under=85 -q
python -m qst.cli vocabulary --check
git diff --check
```

Do not commit, push, tag, publish, approve, or activate unless the user requests the
corresponding action. Report exact commands, results, residual risks, and remote state.
