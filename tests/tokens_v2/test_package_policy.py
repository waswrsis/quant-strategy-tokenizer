from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_strategy_tokenizer.package.manifest import PackageManifest, PackageStrategyManifest
from quant_strategy_tokenizer.tokens_v2 import (
    TokenPackPackageEntryV04,
    TokenPacksPackageSectionV04,
    token_pack_package_section_from_packs,
    verify_token_pack_package_section,
)
from tests.tokens_v2.test_token_pack_v2 import make_pack
from tests.tokens_v2.test_token_spec_v2 import make_spec


def test_legacy_package_manifest_without_token_packs_still_parses() -> None:
    manifest = PackageManifest(
        qst_version="0.1.0",
        strategy=PackageStrategyManifest(name="demo", version=1),
    )

    assert manifest.token_packs is None


def test_package_manifest_records_token_pack_policy() -> None:
    pack = make_pack()
    token_packs = token_pack_package_section_from_packs(
        (pack,),
        embedded_policy="spec_only",
    )
    manifest = PackageManifest(
        qst_version="0.1.0",
        strategy=PackageStrategyManifest(name="demo", version=1),
        token_packs=token_packs,
    )

    assert manifest.token_packs is not None
    assert manifest.token_packs.embedded_policy == "spec_only"
    assert manifest.token_packs.packs[0].pack_id == pack.pack_id
    assert manifest.token_packs.packs[0].embedded is True


def test_embedded_none_policy_rejects_embedded_pack() -> None:
    pack = make_pack()
    entry = token_pack_package_section_from_packs(
        (pack,),
        embedded_policy="spec_only",
    ).packs[0]

    with pytest.raises(ValidationError):
        TokenPacksPackageSectionV04(embedded_policy="none", packs=(entry,))


def test_spec_only_policy_rejects_embedded_executable_code() -> None:
    pack = make_pack(
        tokens=(
            make_spec(
                implementation_ref={"python_entrypoint": "dangerous.module:run"},
            ),
        ),
    ).model_copy(update={"contains_executable_code": True})

    with pytest.raises(ValidationError):
        token_pack_package_section_from_packs((pack,), embedded_policy="spec_only")


def test_spec_and_source_policy_can_record_executable_code_without_execution() -> None:
    pack = make_pack(
        tokens=(
            make_spec(
                implementation_ref={"python_entrypoint": "definitely_missing.module:boom"},
            ),
        ),
    ).model_copy(
        update={
            "contains_executable_code": True,
            "embedded_token_policy": "spec_and_source",
            "embeds_source": True,
        }
    )
    section = token_pack_package_section_from_packs((pack,), embedded_policy="spec_and_source")

    result = verify_token_pack_package_section(section, (pack,))

    assert result.ok
    assert section.packs[0].contains_executable_code is True


def test_verify_package_section_reports_missing_and_hash_mismatch() -> None:
    pack = make_pack()
    missing_section = token_pack_package_section_from_packs((pack,), embedded_policy="none")

    missing_result = verify_token_pack_package_section(missing_section, ())

    assert [diagnostic.code for diagnostic in missing_result.diagnostics] == [
        "QST_V2_PACKAGE_TOKEN_PACK_MISSING"
    ]

    bad_entry = TokenPackPackageEntryV04(
        pack_id=pack.pack_id,
        version=pack.version,
        token_pack_hash="sha256:" + "0" * 64,
        embedded=False,
        contains_executable_code=False,
    )
    mismatch_result = verify_token_pack_package_section(
        TokenPacksPackageSectionV04(embedded_policy="none", packs=(bad_entry,)),
        (pack,),
    )

    assert [diagnostic.code for diagnostic in mismatch_result.diagnostics] == [
        "QST_V2_PACKAGE_TOKEN_PACK_HASH_MISMATCH"
    ]
