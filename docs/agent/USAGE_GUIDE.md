# Usage Guide

## Install and Inspect

```bash
pip install -e ".[dev]"
python -m qst.cli --help
python -m qst.cli vocabulary --check
```

## Validate Strategy Records

```bash
python -m qst.cli validate examples/strategies/kdj_cross_basic.gkr.yaml
python -m qst.cli hash examples/strategies/kdj_cross_basic.gkr.yaml
python -m qst.cli canonicalize examples/strategies/kdj_cross_basic.gkr.yaml --output .local_audit/kdj.canonical.json
```

These commands validate and identify a record. They do not execute or backtest it.

## Build a Strategy Receipt

```python
from pathlib import Path

from qst.admission import admit_strategy_memory
from qst.ir import load_ir_v04_file
from qst.receipts import build_strategy_record_receipt

ir = load_ir_v04_file(Path("examples/strategies/01_ema_cross/strategy.gkr.yaml"))
receipt = build_strategy_record_receipt(
    ir,
    non_goals=(
        "no broker or exchange execution",
        "no backtest or profitability claim",
    ),
)
admission = admit_strategy_memory(receipt)
assert admission.allowed
```

Use the admission result before labelling the strategy as validated agent memory.
Experiment and agent receipts require external evidence; see
[Record-Layer Workflow](RECORD_LAYER_WORKFLOW.md).

For a single CLI summary:

```bash
python -m qst.cli inspect examples/strategies/01_ema_cross/strategy.gkr.yaml --canonical-output .local_audit/ema.canonical.json
```

## Use the FinRobot Sidecar

```python
from pathlib import Path

from qst.integrations.finrobot import FinRobotReadOnlyTools
from qst.storage import ContentAddressedStore

tools = FinRobotReadOnlyTools(ContentAddressedStore(Path(".local_audit/finrobot-store")))
result = tools.strategy_validate(Path("examples/strategies/01_ema_cross/strategy.gkr.yaml"))
identity = tools.strategy_identity(Path("examples/strategies/01_ema_cross/strategy.gkr.yaml"))
```

Always cite returned diagnostics. `not_executable_by_adapter` is an intentional boundary,
not an error to suppress. Read `admission_ready` and `admission_blockers` separately from
the syntax/contract-level `ok` result.

## Coverage Frontier

```bash
python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --json
```

Coverage describes record-layer routability, not runtime, backtest, or profitability.

## Qlib Partial Import

```bash
python -m qst.cli adapter qlib import examples/adapters/qlib/workflow_config_lightgbm_alpha158.yaml --output .local_audit/qlib.gkr.yaml --coverage .local_audit/qlib.coverage.json
python -m qst.cli validate .local_audit/qlib.gkr.yaml
```

The importer is partial and not lossless. It does not import Qlib, run qrun, train a
model, run inference, execute a backtest, or connect to a broker or exchange.

## Authority Profiles

```bash
python -m qst.cli authority profile list
python -m qst.cli authority mode select token_review --profile research-advisory
```

Profile selection records authority policy. It does not turn evidence into approval.

## Legacy v0.4 Runtime

```bash
python -m qst.cli compat-v04 token verify --help
python -m qst.cli compat-v04 token approve --help
python -m qst.cli compat-v04 token execute --help
```

This namespace is compatibility-only and excluded from QST 1.0 product claims.
