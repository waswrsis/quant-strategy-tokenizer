from __future__ import annotations

import inspect
import time

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.agent import search as public_search
from quant_strategy_tokenizer.agent.search import SearchResult, search


def _ids(results: list[SearchResult]) -> set[str]:
    return {result.id for result in results}


def test_search_filters_by_domain() -> None:
    results = search("token", domain="compare")

    assert {"compare.gt", "compare.ge", "compare.lt", "compare.le"} <= _ids(results)
    assert all(result.id.startswith("compare.") for result in results)


def test_search_filters_by_output_type() -> None:
    results = search("token", output_type="Plan")

    assert {"plan.noop", "plan.order_intent"} <= _ids(results)


def test_search_filters_by_input_types() -> None:
    results = search("token", input_types=["Decision"])

    assert {"plan.noop", "plan.order_intent", "decision.map_status"} <= _ids(results)


def test_search_filters_by_state_tag() -> None:
    results = search("token", state_tag="lti_recursive")

    assert _ids(results) == {"smooth.linear_recursive"}


def test_search_filters_by_profile_allowed() -> None:
    results = search("token", profile_allowed="pretrade")

    assert "risk.position_cap" in _ids(results)
    assert "smooth.linear_recursive" in _ids(results)


def test_search_filters_by_uses_token() -> None:
    results = search("recipe", uses_token="smooth.linear_recursive")

    assert "indicator.ewm" in _ids(results)


def test_search_filters_by_fully_verified() -> None:
    results = search("tagspec", fully_verified_only=True)

    assert _ids(results) == {"indicator.ewm"}


def test_search_filters_by_lifecycle() -> None:
    results = search("token", lifecycle=["core_stable", "core_candidate"])

    assert "data.column" in _ids(results)


def test_search_combines_filters_and_empty_result() -> None:
    matches = search(
        "token",
        domain="plan",
        output_type="Plan",
        input_types=["Decision"],
        profile_allowed="pretrade",
        limit=1,
    )
    empty = search("recipe", domain="indicator", output_type="Plan")

    assert len(matches) == 1
    assert matches[0].id in {"plan.noop", "plan.order_intent"}
    assert empty == []


def test_search_limit_defaults_and_override() -> None:
    default_results = search("token")
    limited_results = search("token", limit=2)

    assert len(default_results) == 25
    assert len(limited_results) == 2


def test_agent_public_search_api_and_discovery() -> None:
    results = public_search("recipe", domain="indicator")
    discovered = agent.discover()

    assert "indicator.ewm" in _ids(results)
    assert "search" in discovered["agent_api"]["p3"]  # type: ignore[index]


def test_search_does_not_read_registry_internals_directly() -> None:
    source = inspect.getsource(search)

    assert "_tokens" not in source
    assert "_recipes" not in source
    assert "get_registry" not in source


def test_search_performance_smoke() -> None:
    search("token")

    start = time.perf_counter()
    search("token", output_type="TimeSeries[float]")
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1
