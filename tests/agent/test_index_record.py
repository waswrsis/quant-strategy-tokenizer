from __future__ import annotations

from quant_strategy_tokenizer.agent.index_record import IndexRecord, build_index


def test_token_index_records_include_public_metadata() -> None:
    records = build_index("token")
    by_id = {record.id: record for record in records}

    data_column = by_id["data.column"]

    assert data_column.kind == "token"
    assert data_column.domain == "data"
    assert data_column.input_types == ("Frame",)
    assert data_column.output_type == "TimeSeries[float]"
    assert data_column.state_tag == "stateless"
    assert "pretrade" in data_column.profile_allowed
    assert data_column.raw_metadata["behavior_version"] == 1


def test_recipe_index_records_include_used_tokens() -> None:
    records = build_index("recipe")
    by_id = {record.id: record for record in records}

    ewm = by_id["indicator.ewm"]

    assert ewm.kind == "recipe"
    assert ewm.domain == "indicator"
    assert ewm.input_types == ("TimeSeries[float]",)
    assert ewm.output_type == "TimeSeries[float]"
    assert ewm.uses_tokens == ("smooth.linear_recursive",)


def test_tagspec_index_records_include_verification_state() -> None:
    records = build_index("tagspec")
    by_id = {record.id: record for record in records}

    ewm = by_id["indicator.ewm"]

    assert ewm.kind == "tagspec"
    assert ewm.domain == "indicator"
    assert ewm.fully_verified is True
    assert ewm.raw_metadata["verification_state"] == "fully_verified"


def test_index_record_matches_all_supported_filters() -> None:
    record = IndexRecord(
        kind="recipe",
        id="indicator.ewm",
        version=1,
        domain="indicator",
        input_types=("TimeSeries[float]",),
        output_type="TimeSeries[float]",
        state_tag="stateless",
        profile_allowed=("research", "pretrade"),
        uses_tokens=("smooth.linear_recursive",),
        fully_verified=True,
        lifecycle="core_stable",
    )

    assert record.matches(
        domain="indicator",
        output_type="TimeSeries[float]",
        input_types=["TimeSeries[float]"],
        state_tag="stateless",
        profile_allowed="pretrade",
        uses_token="smooth.linear_recursive",
        fully_verified_only=True,
        lifecycle=["core_stable"],
    )
    assert not record.matches(domain="event")
    assert not record.matches(input_types=["Decision"])
    assert not record.matches(fully_verified_only=True, lifecycle=["experimental"])
