"""Profile policy constants for P1-extended-a validators."""

from __future__ import annotations

from typing import Literal

from quant_strategy_tokenizer.ir.envelope import ProfileLiteral

Purity = Literal["pure", "contextual_read", "external_read", "external_write", "forbidden"]

PURITY_ORDER: dict[str, int] = {
    "pure": 0,
    "contextual_read": 1,
    "external_read": 2,
    "external_write": 3,
    "forbidden": 4,
}

PROFILE_MAX_PURITY: dict[ProfileLiteral, Purity] = {
    "research": "external_read",
    "paper": "external_read",
    "pretrade": "contextual_read",
    "production_guarded": "contextual_read",
}

STRICT_TEMPORAL_PROFILES: set[ProfileLiteral] = {"pretrade", "production_guarded"}
UNSAFE_STRICT_WINDOW_MODES = {"centered", "full_sample", "mixed", "unknown"}
