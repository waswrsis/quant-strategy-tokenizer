"""
quant_strategy_tokenizer.indicators
===================================
Purpose: package namespace for independently callable indicator tokens.
Core idea: Keep each trend, momentum, volatility, volume, structure, breadth, feature, and diagnostic indicator importable and executable without a runner so users can combine only the calculations they need. Assumes indicator modules receive data from the caller and should not own data sourcing or trading decisions.
Inputs: module-specific Request dataclasses containing raw data, params, field specs, extractors, and context.
Outputs: ModuleResult objects containing module-specific Report dataclasses.
Failure semantics: indicator modules fail explicitly on missing fields, invalid parameters, insufficient data, or unavailable optional backends.
Market generalization: indicators operate on mapped numeric fields and do not assume venue, quote, settlement, or asset class.
"""
__all__ = []
