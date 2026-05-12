"""
quant_strategy_tokenizer.filters
================================
Module purpose: package namespace for independently callable filter tokens.
Core idea: Expose filter modules as standalone row/state gates rather than embedding them in a runner. Assumes filters consume external state snapshots and should not calculate indicators or query live systems themselves.
Inputs: module-specific candidate rows, state mappings, params, and runtime context.
Outputs: ModuleResult objects containing accepted/rejected rows or per-symbol decisions.
Failure semantics: filter modules fail explicitly on unusable input and reject rows when configured fail-closed.
Market generalization: filters operate on caller identifiers and metadata without venue assumptions.
"""
__all__ = []
