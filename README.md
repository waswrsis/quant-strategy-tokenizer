# Quant Strategy Tokenizer

Quant Strategy Tokenizer (QST) is a reference implementation of a typed,
canonical strategy representation for quantitative trading research. It turns
strategy YAML into stable IR, hashes, locks, packages, validation artifacts, and
auditable Token System v2 metadata.

QST is not a trading bot, broker adapter, exchange connector, or portfolio
optimizer. The accepted project is a deterministic strategy-kernel foundation:
it is built to make strategy content inspectable, hash-stable, portable, and
safe to validate before any real execution system is attached.

## Status

Project-wide acceptance is complete.

- Final project record: [QST_PROJECT_ACCEPTANCE.md](QST_PROJECT_ACCEPTANCE.md)
- Token System v2 record: [TOKEN_SYSTEM_V2_ACCEPTANCE.md](TOKEN_SYSTEM_V2_ACCEPTANCE.md)
- Hash stability: [docs/ACCEPTANCE/HASH_STABILITY_REPORT.md](docs/ACCEPTANCE/HASH_STABILITY_REPORT.md)
- Security boundaries: [docs/ACCEPTANCE/SECURITY_BOUNDARY_REPORT.md](docs/ACCEPTANCE/SECURITY_BOUNDARY_REPORT.md)
- Known limitations: [docs/ACCEPTANCE/KNOWN_LIMITATIONS.md](docs/ACCEPTANCE/KNOWN_LIMITATIONS.md)

The active kernel target is `qst-ir/0.4` with `qst-canonical/0.4`. Legacy
`qst-ir/0.3` and `qst-ir/0.3.1` remain loadable, verifiable, explainable, and
migratable, but they are not active authoring targets for new v2 work.

The accepted code freeze baseline is:

```text
1ede6998bf442c22102b6a83530ef89a0cdadaaa
```

## Install

QST requires Python 3.11 or newer.

```bash
python -m pip install -e ".[dev]"
```

Optional Parquet support uses `pyarrow`, which is already included in the dev
extra:

```bash
python -m pip install -e ".[parquet]"
```

The package installs a `qst` console script. All commands can also be run with:

```bash
python -m quant_strategy_tokenizer.cli --help
```

## Quick Start

Check the built-in vocabulary:

```bash
qst vocabulary --check
```

Validate and hash a legacy strategy:

```bash
qst validate strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
```

Build and verify a deterministic lock:

```bash
qst lock strategies/kdj_cross_basic.qst.yaml --output qst.lock
qst verify strategies/kdj_cross_basic.qst.yaml --lock qst.lock
```

Create and verify a directory package:

```bash
qst package strategies/kdj_cross_basic.qst.yaml --output out/kdj.qstpkg
qst verify out/kdj.qstpkg
```

Migrate a legacy strategy snapshot to `qst-ir/0.4`:

```bash
qst migrate-ir strategies/kdj_cross_basic.qst.yaml --to qst-ir/0.4 --output out/kdj.v04.qst.yaml
```

Inspect custom-token runtime surfaces:

```bash
qst token verify --help
qst token approve --help
qst token execute --help
```

## Capabilities

QST has two accepted layers: the legacy P0-P4 foundation and Token System v2.

### Legacy P0-P4 Foundation

- Stable YAML strategy loading and canonicalization for `qst-ir/0.3`.
- Three-layer legacy hashes: graph, param, and instance.
- Frozen compatibility checks for the reference strategies.
- Guarded validation profiles, explanations, trace explanations, and repair hints.
- Deterministic `qst.lock` and directory `.qstpkg` packages.
- Package verification, unpacking, strategy search, and fork lineage.
- Artifact schemas for execution reports, backtest evidence, portfolio snapshots,
  adapter manifests, and qstpkg artifact references.
- Frame models for market, feature, signal, and trace data with JSON, CSV,
  pandas, Arrow, and Parquet I/O.
- Universal port protocols, signal extraction, mock adapters, and mock P4b CLI
  flows.

### Token System v2

Token System v2 is the accepted `qst-ir/0.4` kernel foundation:

- Independent v0.4 IR shell and canonical bytes.
- Hash v2 framework for graph, params, instance, signatures, behavior,
  TokenSpecs, TokenPacks, implementation refs, runtime environments, audit
  chains, and expected artifacts.
- Structured TypeSpec and PortSpec models.
- Static temporal rule validation with PV-C artifacts.
- Numeric policy and token evolution policy.
- TokenSpec v2, TokenPack manifests, registry resolution, and qstpkg metadata
  propagation.
- Deterministic state helpers, closed-set FSM helpers, and PV-A state artifacts.
- Decision algebra with true monoids, fold policies, aggregators, and legacy
  reduce classification.
- Panel type-layer metadata, Panel operators, WeightPanel operators, and PV-B
  reference strategies.
- Custom-token verify / approve / grant / execute boundaries and PV-D Kalman
  artifacts.
- Legacy strategy and legacy qstpkg migration tooling to v0.4 snapshots.

## Security Model

The custom-token runtime is deliberately split into separate actions:

```text
verify_integrity -> check_authorization -> approve -> issue grant -> execute
```

Integrity verification checks metadata, hashes, dependencies, implementation
references, runtime environment references, and audit material without importing
or executing custom Python code.

Approval is local security state. It is not portable trust, does not enter
strategy hashes, and is not inherited from qstpkg contents. Execution requires a
short-lived, hash-bound, run-id-bound `ExecutionGrant`.

WP9 v0.1 does not provide a sandbox. A `python_entrypoint` is equivalent to
running approved local Python code.

## Hash Stability

Legacy P0-P4 hashes remain frozen. The accepted reference hashes are recorded in
[docs/ACCEPTANCE/HASH_STABILITY_REPORT.md](docs/ACCEPTANCE/HASH_STABILITY_REPORT.md).

`qst-ir/0.4` hashes are new identities and are not compared for equality with
legacy hashes. Migration records legacy source hashes as lineage evidence and
creates a new v0.4 snapshot identity.

## Repository Map

```text
quant_strategy_tokenizer/
  ir/                     legacy qst-ir/0.3 models, canonicalization, hashing
  ir_v04/                 qst-ir/0.4 model, canonicalization, validation
  hash_v2/                v0.4 hash framework
  types_v2/, ports_v2/    structured v2 type and port contracts
  tokens_v2/              TokenSpec, TokenPack, registry, lock/package metadata
  state_v2/               state and FSM reference semantics
  decision_v2/            decision algebra reference semantics
  panel_v2/               panel, selection, and WeightPanel reference semantics
  custom_runtime_v2/      custom-token integrity, approval, grant, execution
  migration_v2/           legacy-to-v0.4 migration tooling
  package/                qstpkg package and verification support

docs/
  ADR/                    accepted architecture decisions
  JSON_SCHEMAS/           public JSON schemas
  ACCEPTANCE/             final acceptance evidence

fixtures/, expected_traces/, expected_diagnostics/
  deterministic P-Validate inputs and expected artifacts

strategies/
  legacy examples and v0.4 P-Validate strategies

tokenpacks/
  reference custom-token pack artifacts

tests/
  regression, compatibility, package, v2 module, and P-Validate tests
```

Historical project background material is preserved in
[docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md).

## Development Gates

Core local checks:

```bash
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=90
```

Focused compatibility checks:

```bash
python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v
python -m pytest tests/package tests/custom_runtime_v2 tests/migration_v2 -v
python -m quant_strategy_tokenizer.cli vocabulary --check
python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml
```

## Limitations

Accepted limitations are tracked in
[docs/ACCEPTANCE/KNOWN_LIMITATIONS.md](docs/ACCEPTANCE/KNOWN_LIMITATIONS.md).
The most important boundaries are:

- No broad v0.4 runtime execution engine.
- No complete v0.4 authoring CLI.
- No sandboxed custom-token execution.
- No real broker, exchange, vectorbt, qlib, ccxt, mlflow, or backtrader adapter.
- No production portfolio optimizer or risk engine.
- Panel and Weight reference numerics are semantic `float64`, not bit-exact.
- qstpkg contents do not carry portable approval or trust.
- P4b-v2 external adapter design is deferred.

## License

MIT. See [LICENSE](LICENSE).
