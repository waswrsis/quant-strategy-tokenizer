from __future__ import annotations

import re
from pathlib import Path

import yaml

from quant_strategy_tokenizer.hash_v2 import compute_hashes_v2
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir_v04 import canonical_bytes_v04, validate_ir_v04
from quant_strategy_tokenizer.migration_v2 import (
    MIGRATION_TOOL_VERSION,
    migrate_strategy,
    migrate_strategy_file,
    target_core_registry_hash,
)
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
KDJ = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
KDJ_EMA = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def test_kdj_cross_migrates_with_lineage_and_new_identity() -> None:
    legacy = load_strategy_file(KDJ)
    result = migrate_strategy(legacy)

    assert result.ok
    assert result.strategy is not None
    assert result.strategy.ir_version == "qst-ir/0.4"
    assert result.strategy.derived_from is not None
    assert result.strategy.derived_from.kind == "ir_migration"
    assert result.strategy.derived_from.source_instance_hash == compute_hashes(legacy).instance_hash
    assert result.strategy.derived_from.target_core_registry_hash == result.target_core_registry_hash
    assert result.strategy.derived_from.migration_tool_version == MIGRATION_TOOL_VERSION
    assert result.target_hashes is not None
    assert result.target_hashes["instance_hash"] != result.source_hashes["instance_hash"]
    assert validate_ir_v04(result.strategy).ok
    assert canonical_bytes_v04(result.strategy) == canonical_bytes_v04(result.strategy.model_dump(mode="json"))


def test_decision_reduce_v2_maps_to_strict_and() -> None:
    result = migrate_strategy_file(KDJ_EMA)

    assert result.ok
    assert result.strategy is not None
    migrated_tokens = [node.token for node in result.strategy.strategy.nodes]
    assert "decision.strict_and" in migrated_tokens
    assert "decision.reduce" not in migrated_tokens


def test_target_core_registry_hash_is_deterministic() -> None:
    left = target_core_registry_hash()
    right = target_core_registry_hash()

    assert left == right
    assert HASH_RE.fullmatch(left)


def test_unsupported_decision_reduce_returns_diagnostic() -> None:
    raw = yaml.safe_load(KDJ.read_text(encoding="utf-8"))
    for node in raw["graph"]:
        if node["token"] == "decision.reduce":
            node["params"]["policy"] = "any_accept"
            node["params"]["unknown_handling"] = "treat_as_accept"
            break

    result = migrate_strategy(StrategyIR.model_validate(raw))

    assert not result.ok
    assert result.strategy is None
    assert result.diagnostics[0].code == "QST_V2_DECISION_REDUCE_POLICY_NON_MIGRATABLE"


def test_qst_ir_031_source_records_031_lineage() -> None:
    legacy = load_strategy_file(KDJ).model_copy(update={"ir_version": "qst-ir/0.3.1"})
    result = migrate_strategy(legacy)

    assert result.ok
    assert result.strategy is not None
    assert result.strategy.derived_from is not None
    assert result.strategy.derived_from.source_ir_version == "qst-ir/0.3.1"
    assert result.strategy.derived_from.source_instance_hash == compute_hashes(legacy).instance_hash
    assert compute_hashes_v2(result.strategy).instance_hash == result.target_hashes["instance_hash"]
