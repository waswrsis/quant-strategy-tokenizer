from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qst.authority import (
    authority_policy_profile_identity,
    load_authority_policy_profile,
    research_advisory_profile,
    resolve_authority_policy_profile,
    save_authority_policy_profile,
    seal_authority_policy_profile,
    seal_authority_policy_profile_file,
)
from qst.cli import app

ACTOR_ID = "sha256:" + "a" * 64


def test_profile_json_and_yaml_round_trip_deterministically(tmp_path: Path) -> None:
    profile = research_advisory_profile()
    json_path = tmp_path / "research.json"
    yaml_path = tmp_path / "research.yaml"
    save_authority_policy_profile(profile, json_path)
    save_authority_policy_profile(profile, yaml_path)

    assert load_authority_policy_profile(json_path) == profile
    assert load_authority_policy_profile(yaml_path) == profile
    assert resolve_authority_policy_profile("builtin:research-advisory") == profile
    assert resolve_authority_policy_profile(str(json_path)) == profile

    second = tmp_path / "research-second.json"
    save_authority_policy_profile(profile, second)
    assert json_path.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        save_authority_policy_profile(profile, json_path)


def test_profile_draft_reseal_changes_identity(tmp_path: Path) -> None:
    original = research_advisory_profile()
    source = tmp_path / "draft.json"
    output = tmp_path / "sealed.json"
    source.write_text(
        json.dumps(
            {
                **original.model_dump(mode="json"),
                "description": "Project-specific advisory policy.",
            }
        ),
        encoding="utf-8",
    )
    sealed = seal_authority_policy_profile_file(
        source,
        output,
        declared_by_actor_id=ACTOR_ID,
        declaration_reason="Project release policy.",
    )
    assert sealed.profile_hash != original.profile_hash
    assert sealed.origin == "project_local"
    assert sealed.declared_by_actor_id == ACTOR_ID
    assert sealed.profile_hash == authority_policy_profile_identity(sealed)
    assert load_authority_policy_profile(output) == sealed


def test_persisted_profile_cannot_impersonate_builtin_material(tmp_path: Path) -> None:
    original = research_advisory_profile()
    impersonator = seal_authority_policy_profile(
        original.model_copy(
            update={
                "profile_hash": None,
                "description": "Altered while still claiming builtin origin.",
            }
        )
    )
    path = tmp_path / "impersonator.json"
    save_authority_policy_profile(impersonator, path)
    with pytest.raises(ValueError, match="does not match builtin material"):
        load_authority_policy_profile(path)


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("duplicate.json", '{"profile_id":"a","profile_id":"b"}', "duplicate JSON key"),
        ("duplicate.yaml", "profile_id: a\nprofile_id: b\n", "duplicate YAML key"),
        ("cycle.yaml", "profile: &profile\n  child: *profile\n", "must not form cycles"),
    ],
)
def test_profile_loader_rejects_duplicate_keys(
    tmp_path: Path, name: str, content: str, message: str
) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_authority_policy_profile(path)


def test_authority_profile_cli_list_export_validate_and_select(tmp_path: Path) -> None:
    runner = CliRunner()
    listed = runner.invoke(app, ["authority", "profile", "list"])
    assert listed.exit_code == 0
    listing = json.loads(listed.stdout)
    assert [item["profile_id"] for item in listing["profiles"]] == [
        "controlled-release",
        "record-capture",
        "research-advisory",
        "strict-governance",
    ]

    exported_path = tmp_path / "research.yaml"
    exported = runner.invoke(
        app,
        [
            "authority",
            "profile",
            "export",
            "research-advisory",
            "--output",
            str(exported_path),
        ],
    )
    assert exported.exit_code == 0
    validated = runner.invoke(
        app, ["authority", "profile", "validate", str(exported_path)]
    )
    assert validated.exit_code == 0
    assert json.loads(validated.stdout)["ok"] is True

    selected = runner.invoke(
        app,
        [
            "authority",
            "mode",
            "select",
            "token_review",
            "--profile",
            str(exported_path),
        ],
    )
    assert selected.exit_code == 0
    selection = json.loads(selected.stdout)["selection"]
    assert selection["configured_mode"] == "advisory"
    assert selection["effective_mode"] == "advisory"


def test_authority_profile_cli_requires_declared_override_reason() -> None:
    result = CliRunner().invoke(
        app,
        [
            "authority",
            "mode",
            "select",
            "token_review",
            "--profile",
            "research-advisory",
            "--mode-override",
            "enforce",
        ],
    )
    assert result.exit_code == 1
    assert "override requires a reason" in result.stdout

    unknown = CliRunner().invoke(
        app, ["authority", "profile", "show", "builtin:not-a-profile"]
    )
    assert unknown.exit_code == 1
    assert "unknown builtin authority profile" in unknown.stdout


def test_authority_profile_cli_seals_declared_project_profile(tmp_path: Path) -> None:
    runner = CliRunner()
    template = tmp_path / "template.json"
    output = tmp_path / "project.json"
    exported = runner.invoke(
        app,
        [
            "authority",
            "profile",
            "export",
            "research-advisory",
            "--output",
            str(template),
        ],
    )
    assert exported.exit_code == 0
    sealed = runner.invoke(
        app,
        [
            "authority",
            "profile",
            "seal",
            str(template),
            "--output",
            str(output),
            "--declared-by-actor-id",
            ACTOR_ID,
            "--declaration-reason",
            "Project release policy.",
        ],
    )
    assert sealed.exit_code == 0
    profile = load_authority_policy_profile(output)
    assert profile.origin == "project_local"
    assert profile.declared_by_actor_id == ACTOR_ID
