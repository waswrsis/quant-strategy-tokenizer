# Quant Strategy Tokenizer

Quant Strategy Tokenizer is a reference implementation of the construction manual v1.1 with the v1.1.1 patch applied, plus the accepted P1-core, P2, and P3a-0 lock-gate construction stages.

The current implementation keeps the P0 baseline frozen, accepts P1-core, adds P1-extended-a purity and temporal safety validators, implements P2a-0/P2a-1 provenance metadata, P2a-2 deterministic recipe generation, P2a-3 composition validation, P2b mutation, P2c-core execution-plan CSE, an opt-in P2c-extended kernel substitution spike, and the P3a-0 deterministic lock hard gate. It does not include P1-extended-b FSM, TA indicator expansion, max-loss risk controls, a production kernel framework, P3 package artifacts, P3 search, or P3 fork lineage.

The implemented loop covers:

- 25 built-in tokens with behavior contracts
- 9 built-in JSON recipes
- Strategy Content IR loading from YAML
- `_envelope` parsing outside Strategy Content IR
- canonicalization, three-layer hashing, validation, and repair hints
- local execution with trace output
- L1 explanation, trace explanation, versioned agent API, and CLI
- profile promotion from `research` to guarded profiles without changing content hashes
- purity and temporal safety validation
- `indicator.ewm` provenance tags, TagSpec verification, mutation, execution-plan CSE, and opt-in kernel substitution
- deterministic recipe expansion for `signals.dual_ema_cross/v1`
- empirical composition validation for `indicator.ewm/v1`
- deterministic `qst.lock` generation and structural verification

## Project Status

| Layer | Status |
|---|---|
| P0 | frozen |
| P0.1 | hardened |
| P1-core | accepted |
| P1-extended-a | completed |
| P1-extended-b | deferred |
| P2a-0 | accepted |
| P2a-1 | accepted |
| P2a-2 | accepted |
| P2a-3 | accepted |
| P2b-0 | accepted |
| P2b-1 | accepted |
| P2c-core | accepted |
| P2c-extended | accepted |
| P3a-0 lock gate | accepted |
| P3a-1 package | not started |
| P3b search/fork | not started |

## Frozen P0 Baseline

- 17 tokens
- 4 recipes
- `qst-ir/0.3`
- `qst-canonical/0.1`
- Frozen hashes and vocabulary triples recorded in `docs/P0_ACCEPTANCE.md`

## P1-Core Definition

P1-core is the accepted guarded-execution layer on top of the frozen P0 Strategy Content IR.

It includes:

- 25 tokens
- 8 recipes
- Decision six-variant model
- deployment envelope and profile promotion
- risk path validator
- `plan.order_intent`
- `qst promote`
- `qst explain-trace`

P1-core does not alter P0 canonicalization or the frozen P0 hash baseline.

## P2-Core Definition

P2-core is the accepted semantic tooling and execution-planning layer on top of P0/P1. It keeps canonical Strategy Content IR and P0/P1 three-layer hashes stable.

P2-core includes:

| Area | Accepted capabilities |
|---|---|
| P2a semantic provenance and composition | `indicator.ewm/v1` provenance, TagSpec attachment/full verification, deterministic recipe generator DSL, `signals.dual_ema_cross/v1`, recipe contract/fuzzing/metamorphic verification |
| P2b mutation | `qst diff`, `qst mutate`, `ChangeParam`, `InsertBefore`, `ReplaceToken`, `InlineRecipe`, before/after hash reports |
| P2c execution planning | Merkle fingerprints, execution-plan CSE, runtime cache trace evidence, `qst fingerprint` |

P2-core does not include default kernel substitution, production kernel scheduling, plugin/MCP integration, FSM, expanded TA indicator libraries, RL, or HFT execution.

## P2c-Extended Spike

P2c-extended is accepted as an opt-in spike adjacent to P2-core:

- `qst kernel plan`
- `qst execute --kernel-substitution`
- one kernel binding for `indicator.ewm/v1`
- fully verified TagSpec and `allowed_kernels` gate required
- no default runtime substitution
- no canonical IR, hash, or fingerprint-material change

## P3a-0 Lock Gate

P3a-0 is accepted as the deterministic lock hard gate before any P3 package, search, or fork work:

- `qst lock`
- `qst verify`
- canonical JSON `qst.lock`
- structured `VerifyResult`
- strict QST version policy only
- no automatic `qst-ir/0.3` to `0.3.1` rewrite
- structural verification only, not numerical output equivalence

## Current P2a Composition Layer

- Current total vocabulary: 25 tokens, 9 recipes
- Deterministic YAML generator DSL
- Built-in algorithm recipe: `signals.dual_ema_cross/v1`
- CLI expansion: `qst recipe expand`
- Full empirical verification for `indicator.ewm/v1`
- No new primitive token, mutation op, or fully verified `signals.dual_ema_cross` TagSpec

## Current P2b Mutation Layer

- `qst diff`
- `qst mutate`
- `ChangeParam`
- `InsertBefore`
- `ReplaceToken`
- `InlineRecipe`
- before/after hash reports for every mutation
- type-compatible token replacement and recipe output-preserving inlining

## Not In Accepted P0/P1/P2-Core

The following are intentionally not part of the accepted P0/P1/P2-core baseline:

- advanced recipe library beyond `signals.dual_ema_cross/v1`
- production kernel framework beyond the `indicator.ewm/v1` opt-in spike
- FSM
- expanded indicator library
- RL / HFT
- plugin / MCP
- P3 package format
- P3 search index
- P3 fork lineage

Reference strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli execute strategies/kdj_cross_basic.qst.yaml --market examples/sample_market_btc_15m.csv
```

P1-core reference strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile research
python -m quant_strategy_tokenizer.cli promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml
python -m quant_strategy_tokenizer.cli execute /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --market examples/sample_market_btc_15m.csv --profile pretrade --trace-path /tmp/qst_p1_trace.json
python -m quant_strategy_tokenizer.cli explain-trace /tmp/qst_p1_trace.json --level human
```

## P0 Verification

Install in editable mode:

```bash
pip install -e ".[dev]"
```

Run the compatibility checks:

```bash
qst vocabulary --check

qst validate strategies/kdj_cross_basic.qst.yaml
qst canonicalize strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst explain strategies/kdj_cross_basic.qst.yaml --level L1

qst execute strategies/kdj_cross_basic.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --trace-path /tmp/qst_trace.json

cp strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml
sed -i.bak 's/lookback: 9/lookback: 14/' /tmp/kdj_lookback_14.yaml
qst compare strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml
```

Expected behavior:

- `qst vocabulary --check` reports 25 tokens and 9 recipes, while P0 frozen triples remain resolvable.
- `qst validate` exits 0 for the P0 reference strategy.
- `qst hash` prints `graph_hash`, `param_hash`, and `instance_hash`.
- `qst execute` writes the requested trace file.
- `qst compare` keeps `graph_hash` identical when only `lookback` changes, while `param_hash` and `instance_hash` change.
- `qst compare` reports the changed parameter path, for example `recipes.kdj.params.lookback: 9 -> 14`.

## P1-Core Verification

```bash
qst validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile research
qst execute strategies/examples_kdj_with_ema_filter.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --profile research \
  --trace-path /tmp/qst_p1_research_trace.json

qst promote strategies/examples_kdj_with_ema_filter.qst.yaml \
  --to pretrade \
  --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml

qst validate /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --profile pretrade
qst execute /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --profile pretrade \
  --trace-path /tmp/qst_p1_trace.json

qst explain-trace /tmp/qst_p1_trace.json --level human
qst explain-trace /tmp/qst_p1_trace.json --level agent
qst explain-trace /tmp/qst_p1_trace.json --level raw
```

Expected behavior:

- Promotion emits a stable JSON result and writes `_envelope.profile: pretrade` when `--output` is provided.
- Promotion does not change the Strategy Content IR hashes.
- Pretrade validation requires a `risk.*` ancestor before `plan.order_intent`.
- Execution produces a trace containing `decision.reduce/v2`, `risk.position_cap`, and `plan.order_intent`.

## P2-Core Verification

```bash
qst tag verify docs/tagspecs/indicator.ewm.tagspec.yaml
qst tag verify docs/tagspecs/indicator.ewm.tagspec.yaml --level full
qst recipe expand signals.dual_ema_cross --params '{"fast_span":9,"slow_span":21}' --output /tmp/dual_ema_cross.json
qst diff strategies/kdj_cross_basic.qst.yaml strategies/kdj_cross_basic.qst.yaml
qst fingerprint strategies/uses_cse_duplicate_chain.qst.yaml
qst execute strategies/uses_cse_duplicate_chain.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --trace-path /tmp/qst_cse_trace.json
qst explain-trace /tmp/qst_cse_trace.json --level raw
qst kernel plan strategies/uses_ewm_with_provenance.qst.yaml
qst execute strategies/uses_ewm_with_provenance.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --kernel-substitution \
  --trace-path /tmp/qst_kernel_trace.json
qst explain-trace /tmp/qst_kernel_trace.json --level raw
```

Expected behavior:

- `qst tag verify` reports `minimally_attached: true`.
- `qst tag verify --level full` reports `fully_verified: true` for `indicator.ewm/v1`.
- `qst recipe expand` writes a deterministic `signals.dual_ema_cross/v1` recipe using only `indicator.ewm` and `event.cross_above`.
- `qst fingerprint` reports `fp_sha256:*` fingerprints and reuse pairs.
- The CSE strategy trace contains `cache_hit: true` nodes with `reused_from` and `fingerprint`.
- P2c-core CSE happens only in the execution plan layer; canonical IR and P0/P1 hashes remain unchanged.
- `qst kernel plan` reports one eligible `indicator.ewm/v1` kernel for the EWM provenance strategy.
- Opt-in kernel execution writes trace evidence with `kernel_substituted: true`; default execution does not substitute.

## P3a-0 Lock Verification

```bash
qst lock strategies/uses_ewm_with_provenance.qst.yaml \
  --output /tmp/qst.lock \
  --canonical-output /tmp/qst.canonical.json

qst verify strategies/uses_ewm_with_provenance.qst.yaml \
  --lock /tmp/qst.lock \
  --canonical /tmp/qst.canonical.json
```

Expected behavior:

- `qst.lock` is canonical JSON, not YAML.
- Re-running `qst lock` on the same inputs yields byte-identical lock output.
- `qst verify` returns structured JSON with `ok`, `verification_level`, `limitation_note`, and `failures`.
- P3a-0 verification reports `STRUCTURAL` and does not claim numerical output equivalence.
- `qst_version_policy=same_minor` is rejected with `qst_version_policy_unsupported`.

The project experience from the previous repository history is preserved in [docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md), with its supporting asset at [docs/assets/performance-90d.png](docs/assets/performance-90d.png).
