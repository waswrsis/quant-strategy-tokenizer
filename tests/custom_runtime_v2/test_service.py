from __future__ import annotations

import json
from pathlib import Path

from quant_strategy_tokenizer.custom_runtime_v2 import (
    ApprovalRequest,
    ApprovalStore,
    TokenRuntimeContext,
    TokenRuntimeService,
    approval_record_hash,
    audit_chain_hash_for_records,
    load_token_pack,
)
from quant_strategy_tokenizer.custom_runtime_v2.audit import AuditRecord
from quant_strategy_tokenizer.custom_runtime_v2.implementation import source_tree_hash
from quant_strategy_tokenizer.ir_v04 import TokenRefV04

ROOT = Path(__file__).resolve().parents[2]
PACK_DIR = ROOT / "tokenpacks" / "qst-tokenpack-kalman"
TOKEN_REF = TokenRefV04(namespace="my_pack", name="kalman_ema", version=1, behavior_version=1)


def test_integrity_verify_never_imports_custom_module(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    src = pack_dir / "src"
    src.mkdir(parents=True)
    sentinel = tmp_path / "imported.txt"
    (src / "danger_token.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('imported')\n"
        "def run(inputs):\n    return {'filtered': []}\n",
        encoding="utf-8",
    )
    manifest = json.loads((PACK_DIR / "tokenpack.json").read_text(encoding="utf-8"))
    manifest["tokens"][0]["implementation_ref"]["path"] = "src"
    manifest["tokens"][0]["implementation_ref"]["python_entrypoint"] = "danger_token:run"
    manifest["tokens"][0]["implementation_ref"]["expected_hash"] = source_tree_hash(src)
    (pack_dir / "tokenpack.json").write_text(json.dumps(manifest), encoding="utf-8")

    integrity = TokenRuntimeService().verify_integrity(
        load_token_pack(pack_dir),
        TOKEN_REF,
        context=TokenRuntimeContext(base_path=pack_dir),
    )

    assert integrity.ok
    assert not sentinel.exists()


def test_integrity_and_authorization_are_separate_for_pretrade() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)

    integrity = service.verify_integrity(pack, TOKEN_REF, context=TokenRuntimeContext(base_path=PACK_DIR))
    authorization = service.check_authorization(integrity, profile="pretrade")

    assert integrity.ok
    assert authorization.status == "requires_approval"
    assert [diagnostic.code for diagnostic in authorization.diagnostics] == [
        "QST_V2_CUSTOM_TOKEN_PRETRADE_REQUIRES_APPROVAL"
    ]


def test_profile_bound_approval_does_not_cross_to_pretrade() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    integrity = service.verify_integrity(pack, TOKEN_REF, context=TokenRuntimeContext(base_path=PACK_DIR))
    request = _approval_request(integrity, profile="research")
    _, store = service.approve_token_pack(request, approval_store=ApprovalStore())

    assert service.check_authorization(integrity, profile="research", approval_store=store).ok
    pretrade = service.check_authorization(integrity, profile="pretrade", approval_store=store)

    assert not pretrade.ok
    assert pretrade.status == "requires_approval"


def test_execute_requires_grant_and_validates_output() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    context = TokenRuntimeContext(base_path=PACK_DIR, profile="research", run_id="unit")
    integrity = service.verify_integrity(pack, TOKEN_REF, context=context)
    _, store = service.approve_token_pack(_approval_request(integrity), approval_store=ApprovalStore())
    authorization = service.check_authorization(integrity, profile="research", approval_store=store)
    grant = service.issue_execution_grant(integrity, authorization, run_id="unit")

    result = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0, 2.0, 3.0], "alpha": 0.5},
        grant=grant,
        context=context,
        approval_store=store,
    )

    assert result.ok
    assert result.output == {"filtered": [1.0, 1.5, 2.25]}
    assert result.audit_records

    bad_grant = grant.model_copy(update={"implementation_ref_hash": "sha256:" + "0" * 64})
    bad = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0]},
        grant=bad_grant,
        context=context,
        approval_store=store,
    )

    assert not bad.ok
    assert "QST_V2_EXECUTION_GRANT_HASH_MISMATCH" in [d.code for d in bad.diagnostics]


def test_execute_rejects_non_canonical_output(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    src = pack_dir / "src"
    src.mkdir(parents=True)
    (src / "bad_token.py").write_text(
        "def run(inputs):\n    return {'filtered': [float('nan')]}\n",
        encoding="utf-8",
    )
    manifest = json.loads((PACK_DIR / "tokenpack.json").read_text(encoding="utf-8"))
    manifest["tokens"][0]["implementation_ref"]["path"] = "src"
    manifest["tokens"][0]["implementation_ref"]["python_entrypoint"] = "bad_token:run"
    manifest["tokens"][0]["implementation_ref"]["expected_hash"] = source_tree_hash(src)
    (pack_dir / "tokenpack.json").write_text(json.dumps(manifest), encoding="utf-8")
    pack = load_token_pack(pack_dir)
    service = TokenRuntimeService()
    context = TokenRuntimeContext(base_path=pack_dir, profile="research", run_id="bad")
    integrity = service.verify_integrity(pack, TOKEN_REF, context=context)
    _, store = service.approve_token_pack(_approval_request(integrity), approval_store=ApprovalStore())
    authorization = service.check_authorization(integrity, profile="research", approval_store=store)
    grant = service.issue_execution_grant(integrity, authorization, run_id="bad")

    result = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0]},
        grant=grant,
        context=context,
        approval_store=store,
    )

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "QST_V2_CUSTOM_TOKEN_OUTPUT_NOT_CANONICAL_JSON"
    ]


def test_audit_chain_excludes_wall_clock_timestamp() -> None:
    base = AuditRecord(
        action="approve",
        token_ref=TOKEN_REF.model_dump(mode="json"),
        profile="research",
        outcome="ok",
        hashes={"token_pack_hash": "sha256:" + "1" * 64},
        recorded_at="2026-05-15T00:00:00Z",
    )
    changed_time = base.model_copy(update={"recorded_at": "2026-05-15T00:01:00Z"})
    changed_semantic = base.model_copy(update={"outcome": "changed"})

    assert audit_chain_hash_for_records([base]) == audit_chain_hash_for_records([changed_time])
    assert audit_chain_hash_for_records([base]) != audit_chain_hash_for_records([changed_semantic])


def test_approval_store_roundtrip(tmp_path: Path) -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    integrity = service.verify_integrity(pack, TOKEN_REF, context=TokenRuntimeContext(base_path=PACK_DIR))
    record, store = service.approve_token_pack(_approval_request(integrity), approval_store=ApprovalStore())
    path = tmp_path / "approvals.json"

    store.save(path)
    loaded = ApprovalStore.load(path)

    assert loaded.records == (record,)
    assert approval_record_hash(record).startswith("sha256:")


def _approval_request(integrity: object, profile: str = "research") -> ApprovalRequest:
    assert hasattr(integrity, "token_ref")
    return ApprovalRequest(
        token_ref=integrity.token_ref,
        profile=profile,  # type: ignore[arg-type]
        approved_by="unit",
        allow_token=True,
        ack_risk=True,
        approved_risk_level=integrity.risk_level,
        token_spec_hash=integrity.token_spec_hash,
        token_pack_hash=integrity.token_pack_hash,
        implementation_ref_hash=integrity.implementation_ref_hash,
        runtime_environment_hash=integrity.runtime_environment_hash,
    )
