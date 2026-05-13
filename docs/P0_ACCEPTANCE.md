# P0 Acceptance Record

Date: 2026-05-13
Accepted commit: 1827625eea165af47fb6f2fb797db1aba7c64368

## Local Checks

```bash
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80

qst vocabulary --check
qst validate strategies/kdj_cross_basic.qst.yaml
qst canonicalize strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst explain strategies/kdj_cross_basic.qst.yaml --level L1
qst execute strategies/kdj_cross_basic.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --trace-path /tmp/qst_trace.json
qst compare strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml

# Expects exit 1 with type_mismatch + repair_hint.
qst validate strategies/broken_no_lift.qst.yaml

python -c "import quant_strategy_tokenizer.agent as a; r = a.discover(); print(r['qst_version'])"
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
```

Result: PASS

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25818386598
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Notes

- P0.1 hardening patches applied.
- P1 has not started.
- P0 vocabulary remains frozen at 17 tokens and 4 recipes.

## Frozen Reference Values (Immutable; P1 Forbidden To Alter)

### Reference Strategy Hashes

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash:    sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947
- param_hash:    sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28
- instance_hash: sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d

`strategies/broken_no_lift.qst.yaml`:

- Expected validation result: failures contains `kind=type_mismatch`
- Expected repair_hint: present, suggests inserting `decision.lift_bool`

### IR / Canonical Versions

- ir_version:        qst-ir/0.3
- canonical_version: qst-canonical/0.1

### Frozen Vocabulary (17 Tokens, 4 Recipes)

P0 tokens `(id, version, behavior_version)`:

```text
data.column                 v1  bv1
data.shift                  v1  bv1
window.max                  v1  bv1
window.min                  v1  bv1
smooth.linear_recursive     v1  bv1
math.add                    v1  bv1
math.sub                    v1  bv1
math.mul                    v1  bv1
math.div                    v1  bv1
math.linear_combination     v1  bv1
compare.gt                  v1  bv1
compare.le                  v1  bv1
logic.and                   v1  bv1
norm.range_position         v1  bv1
decision.lift_bool          v1  bv1
decision.reduce             v1  bv1
plan.noop                   v1  bv1
```

P0 recipes `(id, version)`:

```text
indicator.ewm        v1
indicator.rma        v1
indicator.kdj        v1
event.cross_above    v1
```

### Coverage

- Threshold: 80%
- Actual at commit 1827625: 84.80%

### Behavior Contracts Snapshot

- Total behavior contracts at P0 acceptance: 34
- Golden collection at P0 acceptance: 35 tests (34 contracts + registry smoke)
- All passing.

## File Status

After P1 starts, this file becomes **append-only**. The "Frozen Reference Values" section above is locked. Any change to those values must be made via:

1. A new section dated and labeled "v0.2 acceptance" (etc.)
2. The original P0 section preserved verbatim
3. An ADR documenting why backward compatibility is being broken

## P1-Core Acceptance Candidate

Date: 2026-05-13
Commit: 644751e73ebe45a97022435281d9d497a2f84834

### P0 Backward Compatibility

- `tests/e2e/test_p0_p1_backward_compat.py`: PASS locally
- P0 graph_hash / param_hash / instance_hash unchanged: PASS locally
- P0 frozen token triples remain resolvable: PASS locally
- P0 frozen recipe pairs remain resolvable: PASS locally

### P1-Core Vocabulary

- Total tokens: 25
- Total recipes: 8
- New P1-core tokens:
  - `decision.reduce/v2`
  - `decision.map_status`
  - `risk.position_cap`
  - `risk.notional_cap`
  - `state.read_field`
  - `plan.order_intent`
  - `compare.ge`
  - `compare.lt`
- New P1-core recipes:
  - `event.threshold_above`
  - `event.threshold_below`
  - `gate.elapsed_threshold`
  - `gate.cooldown`

### P1-Core Local Checks

- `ruff check .`
- `mypy quant_strategy_tokenizer tests`
- `mypy --strict quant_strategy_tokenizer`
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`
- `pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`
- `qst validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile pretrade`
- `qst promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml`
- `qst explain-trace /tmp/qst_p1_pretrade_trace.json --level human`

Result: PASS

CI: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25824730331
