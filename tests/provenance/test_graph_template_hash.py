from __future__ import annotations

from quant_strategy_tokenizer.provenance.graph_hash import recipe_graph_template_hash


def test_indicator_ewm_graph_template_hash_is_stable() -> None:
    assert (
        recipe_graph_template_hash("indicator.ewm", 1)
        == "sha256:447b7f214a109b55ce306cf6330274b787db2af81c406e5f28781f87e5527dd8"
    )
