# Quant Strategy Tokenizer

Quant Strategy Tokenizer is a reference implementation of the construction manual v1.1 with the v1.1.1 patch applied, plus the accepted P1-core, P2, P3, and P4-core construction stages. Token System v2 WP0-WP8a are accepted under the v1.0.3 construction standard.

The current implementation keeps the P0 baseline frozen, accepts P1-core, adds P1-extended-a purity and temporal safety validators, implements P2a-0/P2a-1 provenance metadata, P2a-2 deterministic recipe generation, P2a-3 composition validation, P2b mutation, P2c-core execution-plan CSE, an opt-in P2c-extended kernel substitution spike, the P3a-0 deterministic lock hard gate, the P3a-1 directory package format, P3b-0 registry search, P3b-1 fork lineage, and P4-core artifacts, frames, qstpkg artifact extension, ports, signal extraction, mock adapters, and P4b CLI. It does not include P1-extended-b FSM, TA indicator expansion, max-loss risk controls, a production kernel framework, P4c real adapter repositories, P4d semantic detokenize, P4+ full-text package search, or numerical equivalence verification.

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
- directory-based `.qstpkg` packages with package/unpack/verify
- on-demand token/recipe/TagSpec search from public registries
- `qst fork` lineage metadata with `qst-ir/0.3.1`
- P4 artifact schemas, artifact identity, and strict DecimalString values
- QST frame models with JSON, CSV, pandas, Arrow, and Parquet I/O
- qstpkg artifact references and artifact verification
- Universal Port protocols, `execute_to_signals()`, local mock adapters, and P4b CLI
- Token System v2 state reference helpers for basic state tokens and closed-set FSMs
- PV-A state-heavy reference cases with deterministic expected traces and hashes
- Token System v2 Decision Algebra reference semantics and TokenPack metadata
- Token System v2 Panel detail design gate schemas and design record

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
| P3a-1 package | accepted |
| P3b-0 search | accepted |
| P3b-1 fork lineage | accepted |
| P4a-0 artifact gate | accepted |
| P4a-1 frames | accepted |
| P4a-2 qstpkg artifacts | accepted |
| P4b-0 ports | accepted |
| P4b-1 mock adapters | accepted |
| P4c real adapters | external repos / not started |
| P4d semantic detokenize | not started |
| Token System v2 WP0 ADR Gate | accepted under v1.0.3 |
| Token System v2 WP1 qst-ir/0.4 shell | accepted under v1.0.3 |
| Token System v2 WP2 TypeSpec + PortSpec | accepted under v1.0.3 |
| Token System v2 WP3 PortTemporalSpec + PV-C | accepted under v1.0.3 |
| Token System v2 WP4 NumericPolicy + TokenEvolutionPolicy | accepted under v1.0.3 |
| Token System v2 WP5 TokenSpec v2 + Registry + TokenPack | accepted under v1.0.3 |
| Token System v2 WP5b Lock + Package Integration | accepted under v1.0.3 |
| Token System v2 WP6a State Basic | accepted under v1.0.3 |
| Token System v2 WP6b State FSM | accepted under v1.0.3 |
| Token System v2 WP6c State Recipes + PV-A | accepted under v1.0.3 |
| Token System v2 WP7 Decision Algebra | accepted under v1.0.3 |
| Token System v2 WP8a Panel Detail Design Gate | accepted under v1.0.3 |
| Token System v2 WP8b Panel Type Layer | not started |
| Token System v2 WP8c Panel Operators | not started |
| Token System v2 WP8d Weight Operators | not started |
| Token System v2 WP8e Panel Recipes + PV-B | not started |

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

## P3a-1 Package Format

P3a-1 is accepted as a directory-based portable artifact layer:

- `qst package`
- `qst unpack`
- `qst verify <pkg_dir>`
- `.qstpkg/manifest.yaml`
- `.qstpkg/qst.lock` as canonical JSON
- `.qstpkg/strategies/source.qst.yaml`
- `.qstpkg/strategies/canonical.json`
- optional fixture hashes for `market.csv` and `expected_trace.json`
- `SEMANTIC_TRACE` verification level when expected trace fixtures are present

## P4-Core Definition

P4-core is the accepted universal artifact, frame, package-artifact, port, and mock-adapter layer. It is additive over P0/P1/P2/P3 and does not change Strategy Content IR canonicalization, three-layer hashes, `qst.lock`, mutation, search, fork, CSE, kernel substitution, or `qst execute`.

P4-core includes:

| Area | Accepted capabilities |
|---|---|
| P4a artifacts | `QSTArtifact`, artifact identity, strict `DecimalString`, `ExecutionReport`, `BacktestEvidence`, `PortfolioSnapshot`, `AdapterManifest`, draft 2020-12 schemas |
| P4a frames | `MarketFrame`, `SignalFrame`, `FeatureFrame`, `TraceLog`, stable frame hashes, JSON/CSV/pandas/Arrow/Parquet round trips, strict multi-symbol MarketFrame alignment |
| P4a qstpkg artifacts | additive `.qstpkg` artifact references, `qst pkg add-artifact`, `qst pkg verify-artifacts`, automatic artifact verification in `qst verify <pkg_dir>` |
| P4b ports | Universal Port protocols, `SignalExtractionPolicy`, `execute_to_signals()`, local adapter discovery foundation |
| P4b mock adapters and CLI | five local mock adapters, `qst adapter`, `qst load market`, `qst backtest`, `qst submit-plan`, `qst poll-execution`, `qst track` |

P4-core does not include P4c real adapters, production broker or exchange integration, MCP, P4d semantic detokenize, or numerical equivalence proof. Real adapters belong in independent `qst-adapter-*` repositories.

P4b-old ports, signal extraction, mock adapters, and CLI are accepted legacy infrastructure. Token System v2 supersedes P4b-old for future adapter expansion; P4b-v2 is deferred as a standalone design after Token System v2 acceptance.

## Token System v2 Roadmap

Token System v2 is the next kernel-level refactor. It targets `qst-ir/0.4` and `qst-canonical/0.4`.

The v1.0.3 construction standard supersedes the earlier Token System v2 WP0-WP2 plans. WP0 ADR Gate is accepted with six ADRs and records:

- `qst-ir/0.4` as the only future active authoring target.
- `qst-ir/0.3` and `qst-ir/0.3.1` as legacy load / verify / explain / migrate inputs.
- Legacy IR as invalid for new token, recipe, adapter, mutation, or fork output once v2 migration is active.
- No sandbox for custom `python_entrypoint` tokens in v0.1.
- Embedded P-Validate gates for temporal safety, state, panel, and custom token work.
- Panel layer detail design, hash stability milestones, and TokenPack propagation/package policy.

WP1 is accepted and adds the independent `qst-ir/0.4` shell, `qst-canonical/0.4` canonical bytes, hash v2 framework, `validation_v2`, `profile_v2`, explicit schema-version shell material, and read-only legacy boundary loaders.

WP2 is accepted and adds structured `TypeSpec`, `ValueType`, `IntrinsicTemporalSpec`, `PortSignature`, `InputSpec`, `OutputSpec`, Panel shell fields, `StrategyIRV04.capabilities`, canonical `NodeV04.token_ref`, and token-ref-aware signature hashing.

WP3 is accepted and adds `TemporalRule`, v0.4 static temporal validation, and PV-C expected diagnostics/traces.

WP4 is accepted and adds `NumericPolicy`, `TokenEvolutionPolicy`, lifecycle status hash material, numeric risk profile decisions, behavior-hash material helpers, and `docs/TOKEN_EVOLUTION_POLICY.md`. It does not add WP5 TokenSpec v2 registry, token packs, migration tooling, runtime execution, Panel behavior, custom token runtime, or v0.4 CLI authoring.

WP5 is accepted and adds `TokenSpecV2`, `TokenPackManifestV2`, deterministic TokenPack dependency validation, `TokenRegistryV2`, typed TokenSpec/TokenPack hash helpers, and JSON schemas.

WP5b is accepted and adds future `qst-lock/0.4` token hash entries, TokenPack dependency lock entries, qstpkg `token_packs` manifest metadata, and deterministic missing-pack/hash-mismatch diagnostics. It verifies metadata only and never executes embedded source. It does not add custom token execution, source-tree packaging layout, migration tooling, runtime integration, Panel behavior, or v0.4 CLI authoring.

WP6a is accepted and adds deterministic v0.4 state reference helpers, `StatePolicy`, state transition traces, `ReducerRegistry`, and the `qst-tokenpack-state-basic/0.1.0` metadata pack for `core.state.delay`, `core.state.accumulate`, and `core.state.edge_detect`. It does not add FSM, state recipes, PV-A, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, or v0.4 CLI authoring.

WP6b is accepted and adds closed-set FSM reference semantics, `FSMDefinition`, `FSMTransition`, transition traces, deterministic replay checks, and the `qst-tokenpack-state-fsm/0.1.0` metadata pack for `core.state.fsm`. It does not add state recipes, PV-A, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, or v0.4 CLI authoring.

WP6c is accepted and adds PV-A state-heavy reference strategy artifacts, deterministic fixtures, expected diagnostics/traces, and expected artifact hashes for cooldown, market freeze, circuit breaker, observe period, and minimal slot budget cases. It does not add v0.4 runtime execution, legacy recipes, Decision Algebra, Panel behavior, custom token runtime, migration tooling, or v0.4 CLI authoring.

WP7 is accepted and adds v0.4 Decision Algebra models, true monoids, fold policies, aggregators, legacy reduce migration classification, and the `qst-tokenpack-decision-algebra/0.1.0` metadata pack. It does not add legacy runtime execution, legacy token registration, strategy mutation, Panel behavior, custom token runtime, migration tooling, or v0.4 CLI authoring.

WP8a is accepted as the Panel Detail Design Gate. It adds draft schemas and the design record for sparse logical Panel representation, UniverseMask, MissingPolicy, GroupSpec, SelectionPanel / WeightPanel boundaries, single-factor residualize, Panel temporal joins, and Panel / State constraints. It does not alter `TypeSpec`, enable the `panel` capability, add Panel operators, add Panel TokenSpecs or TokenPacks, or introduce v0.4 runtime execution.

The authoritative roadmap is [docs/TOKEN_SYSTEM_V2_ROADMAP.md](docs/TOKEN_SYSTEM_V2_ROADMAP.md).

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

## Not In Accepted P0/P1/P2/P3/P4-Core

The following are intentionally not part of the accepted P0/P1/P2/P3/P4-core baseline:

- advanced recipe library beyond `signals.dual_ema_cross/v1`
- production kernel framework beyond the `indicator.ewm/v1` opt-in spike
- persistent package search indexes
- P4+ full-text or cross-package search
- P4c real adapter repositories inside `qst-core`
- P4d semantic detokenize
- production broker, exchange, vectorbt, qlib, mlflow, or backtrader integrations
- numerical equivalence proof
- FSM
- expanded indicator library
- RL / HFT
- plugin / MCP

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

## P3a-1 Package Verification

```bash
qst package strategies/uses_ewm_with_provenance.qst.yaml \
  --output /tmp/uses_ewm.qstpkg

qst verify /tmp/uses_ewm.qstpkg

qst unpack /tmp/uses_ewm.qstpkg \
  --output /tmp/uses_ewm_unpacked
```

Expected behavior:

- `.qstpkg/qst.lock` remains canonical JSON.
- Package manifests are YAML and do not change the lock format.
- `qst verify <pkg_dir>` returns the same structured `VerifyResult` shape as lock verification.
- Packages without `expected_trace.json` verify at `STRUCTURAL` level.
- Packages with `expected_trace.json` verify at `SEMANTIC_TRACE` level when both full and semantic trace hashes match.
- `SEMANTIC_TRACE` still does not prove numerical output equivalence.

## P3b Search And Fork Verification

```bash
qst search token --output-type "TimeSeries[float]"
qst search recipe --uses-token smooth.linear_recursive --limit 20
qst search tagspec --fully-verified

qst fork strategies/kdj_cross_basic.qst.yaml \
  --new-id kdj_variant \
  --out /tmp/kdj_variant.qst.yaml

qst hash strategies/kdj_cross_basic.qst.yaml
qst hash /tmp/kdj_variant.qst.yaml
```

Expected behavior:

- Search scans public token, recipe, and TagSpec registries in memory.
- Search does not write a persistent index file.
- `qst search tagspec --fully-verified` returns the verified `indicator.ewm/v1` TagSpec.
- `qst fork` is the only command that emits `qst-ir/0.3.1`.
- Forked strategies include inert `derived_from` metadata.
- Existing commands preserve `qst-ir/0.3`.
- Three-layer hashes and execution fingerprints ignore `derived_from`.

## P4-Core Verification

```bash
qst adapter list
qst adapter verify mock-execution

qst load market \
  --source /tmp/qst_market_frame.csv \
  --symbols BTC/USDT \
  --output /tmp/qst_market_frame.json

qst backtest strategies/uses_ewm_with_provenance.qst.yaml \
  --adapter mock \
  --market /tmp/qst_market_frame.json \
  --output /tmp/qst_mock_backtest.qstpkg

qst verify /tmp/qst_mock_backtest.qstpkg

qst submit-plan /tmp/qst_plan.json \
  --adapter mock-execution \
  --confirm \
  --output /tmp/qst_execution_report.json

qst poll-execution mock-execution-report-id \
  --adapter mock-execution \
  --output /tmp/qst_execution_poll.json

qst track /tmp/qst_mock_backtest.qstpkg \
  --adapter mock-experiment \
  --run-name p4-core-smoke
```

Expected behavior:

- `qst adapter list` reports `mock-backtest`, `mock-csv-market`, `mock-execution`, `mock-experiment`, and `mock-parquet-market`.
- `qst adapter verify mock-execution` reports `execution=true`.
- `qst load market` writes canonical `MarketFrame` JSON.
- `qst backtest` builds a `.qstpkg` and inserts `BacktestEvidence` through the P4a-2 artifact extension.
- `qst verify <pkg_dir>` validates package artifacts in addition to P3 lock/package checks.
- `qst submit-plan`, `qst poll-execution`, and `qst track` use local mock adapters only and do not access external networks.

The project experience from the previous repository history is preserved in [docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md), with its supporting asset at [docs/assets/performance-90d.png](docs/assets/performance-90d.png).
