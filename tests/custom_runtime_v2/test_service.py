from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

import pytest

from quant_strategy_tokenizer.custom_runtime_v2 import (
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStore,
    TokenRuntimeContext,
    TokenRuntimeService,
    approval_record_hash,
    audit_chain_hash_for_records,
    load_token_pack,
)
from quant_strategy_tokenizer.custom_runtime_v2.audit import AuditRecord
from quant_strategy_tokenizer.custom_runtime_v2.implementation import (
    ImplementationRef,
    resolve_implementation_hash,
    source_tree_hash,
)
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


def test_approval_requires_allow_token_and_ack_risk() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    integrity = service.verify_integrity(pack, TOKEN_REF, context=TokenRuntimeContext(base_path=PACK_DIR))

    for field in ("allow_token", "ack_risk"):
        request = _approval_request(integrity).model_copy(update={field: False})
        with pytest.raises(ValueError, match="allow_token=True and ack_risk=True"):
            service.approve_token_pack(request, approval_store=ApprovalStore())

        unsafe_record = ApprovalRecord(approval_id=f"unsafe_{field}", **request.model_dump(mode="json"))
        authorization = service.check_authorization(
            integrity,
            profile="research",
            approval_store=ApprovalStore(records=(unsafe_record,)),
        )
        assert not authorization.ok
        assert authorization.status == "requires_approval"


def test_execute_requires_grant_and_validates_output() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    context = TokenRuntimeContext(
        base_path=PACK_DIR,
        profile="research",
        run_id="unit",
        current_time_utc="2026-05-15T00:00:00Z",
    )
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


def test_execute_rejects_expired_or_wrong_run_grant() -> None:
    service = TokenRuntimeService()
    pack = load_token_pack(PACK_DIR)
    context = TokenRuntimeContext(base_path=PACK_DIR, profile="research", run_id="unit")
    integrity = service.verify_integrity(pack, TOKEN_REF, context=context)
    _, store = service.approve_token_pack(_approval_request(integrity), approval_store=ApprovalStore())
    authorization = service.check_authorization(integrity, profile="research", approval_store=store)
    grant = service.issue_execution_grant(integrity, authorization, run_id="unit")

    wrong_run = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0]},
        grant=grant,
        context=context.model_copy(update={"run_id": "other"}),
        approval_store=store,
    )
    assert not wrong_run.ok
    assert "QST_V2_EXECUTION_GRANT_RUN_ID_MISMATCH" in [d.code for d in wrong_run.diagnostics]

    expired_grant = grant.model_copy(update={"expires_at": "2000-01-01T00:00:00Z"})
    expired = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0]},
        grant=expired_grant,
        context=context,
        approval_store=store,
    )
    assert not expired.ok
    assert "QST_V2_EXECUTION_GRANT_EXPIRED" in [d.code for d in expired.diagnostics]


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


def test_execute_rejects_extra_output_port(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    src = pack_dir / "src"
    src.mkdir(parents=True)
    (src / "extra_token.py").write_text(
        "def run(inputs):\n    return {'filtered': [1.0], 'secret_debug': ['leak']}\n",
        encoding="utf-8",
    )
    manifest = json.loads((PACK_DIR / "tokenpack.json").read_text(encoding="utf-8"))
    manifest["tokens"][0]["implementation_ref"]["path"] = "src"
    manifest["tokens"][0]["implementation_ref"]["python_entrypoint"] = "extra_token:run"
    manifest["tokens"][0]["implementation_ref"]["expected_hash"] = source_tree_hash(src)
    (pack_dir / "tokenpack.json").write_text(json.dumps(manifest), encoding="utf-8")
    pack = load_token_pack(pack_dir)
    service = TokenRuntimeService()
    context = TokenRuntimeContext(base_path=pack_dir, profile="research", run_id="extra")
    integrity = service.verify_integrity(pack, TOKEN_REF, context=context)
    _, store = service.approve_token_pack(_approval_request(integrity), approval_store=ApprovalStore())
    authorization = service.check_authorization(integrity, profile="research", approval_store=store)
    grant = service.issue_execution_grant(integrity, authorization, run_id="extra")

    result = service.execute_custom_token(
        pack,
        TOKEN_REF,
        inputs={"series": [1.0]},
        grant=grant,
        context=context,
        approval_store=store,
    )

    assert not result.ok
    assert result.output is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "QST_V2_CUSTOM_TOKEN_OUTPUT_EXTRA_PORT"
    ]


def test_installed_distribution_hash_uses_file_content_when_record_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_file = tmp_path / "demo_pkg.py"
    package_file.write_text("VALUE = 1\n", encoding="utf-8")

    class FakeDistribution:
        version = "1.0.0"
        files = ("demo_pkg.py",)

        def locate_file(self, file: object) -> Path:
            return tmp_path / str(file)

    monkeypatch.setattr(importlib.metadata, "distribution", lambda _name: FakeDistribution())
    ref = ImplementationRef(kind="installed_distribution", distribution="demo")

    first, first_code = resolve_implementation_hash(ref, base_path=tmp_path)
    package_file.write_text("VALUE = 2\n", encoding="utf-8")
    second, second_code = resolve_implementation_hash(ref, base_path=tmp_path)

    assert first_code == "QST_V2_DISTRIBUTION_RECORD_INCOMPLETE"
    assert second_code == "QST_V2_DISTRIBUTION_RECORD_INCOMPLETE"
    assert first != second


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
