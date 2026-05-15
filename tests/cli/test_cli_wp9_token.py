from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "tokenpacks" / "qst-tokenpack-kalman"
TOKEN_REF = "my_pack.kalman_ema/v1/bv1"


def test_cli_token_verify_approve_execute_are_separate(tmp_path: Path) -> None:
    runner = CliRunner()
    approvals = tmp_path / "approvals.json"
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"series": [1, 2, 3], "alpha": 0.5}), encoding="utf-8")

    verify = runner.invoke(
        app,
        [
            "token",
            "verify",
            TOKEN_REF,
            "--pack",
            str(PACK),
            "--profile",
            "pretrade",
            "--approvals",
            str(approvals),
        ],
    )
    assert verify.exit_code == 0
    verify_payload = json.loads(verify.output)
    assert verify_payload["integrity"]["ok"] is True
    assert verify_payload["authorization"]["status"] == "requires_approval"

    approved = runner.invoke(
        app,
        [
            "token",
            "approve",
            TOKEN_REF,
            "--pack",
            str(PACK),
            "--profile",
            "pretrade",
            "--approved-by",
            "unit",
            "--allow-token",
            "--ack-risk",
            "--approvals",
            str(approvals),
        ],
    )
    assert approved.exit_code == 0, approved.output

    executed = runner.invoke(
        app,
        [
            "token",
            "execute",
            TOKEN_REF,
            "--pack",
            str(PACK),
            "--profile",
            "pretrade",
            "--inputs-file",
            str(inputs),
            "--approvals",
            str(approvals),
            "--run-id",
            "cli-test",
        ],
    )
    assert executed.exit_code == 0, executed.output
    executed_payload = json.loads(executed.output)
    assert executed_payload["output"] == {"filtered": [1.0, 1.5, 2.25]}

    listed = runner.invoke(app, ["token", "approvals", "list", "--approvals", str(approvals)])
    assert listed.exit_code == 0
    assert len(json.loads(listed.output)["records"]) == 1

    revoked = runner.invoke(
        app,
        ["token", "approvals", "revoke", TOKEN_REF, "--profile", "pretrade", "--approvals", str(approvals)],
    )
    assert revoked.exit_code == 0
    assert json.loads(revoked.output)["records"] == 0
