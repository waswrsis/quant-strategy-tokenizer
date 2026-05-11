"""
quant_strategy_tokenizer.filters
========================
Module purpose: atomic, reusable candidate filters.
Core idea: each filter accepts a candidate list plus caller-supplied state or
features, then returns accepted/rejected records with detailed reasons.
Inputs: module-specific Request dataclasses.
Configuration: pass candidates plus caller-supplied state mappings into each
filter Request; use each filter's `*Params` dataclass to set field names,
thresholds, accepted values, and fail-closed behavior.
Outputs: ModuleResult containing accepted/rejected symbols and diagnostics.
Failure semantics: unknown required state is rejected/fail-closed by default.
Market generalization: filters operate on generic symbol identifiers and do
not assume asset class, venue, quote, or settlement.
"""

__all__ = []
