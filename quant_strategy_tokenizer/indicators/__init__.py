"""
quant_strategy_tokenizer.indicators
===========================
Module purpose: independently callable atomic indicator modules.
Core idea: users can compose EMA, ATR, VWAP, CHOP and other calculations in
any order because each module accepts raw input and returns detailed output.
Inputs: module-specific Request dataclasses.
Configuration: pass raw data plus `DataFrameSpec`/`ExtractorSpec` into each
indicator Request; use each indicator's `*Params` dataclass to set windows,
field names, calculation mode, and diagnostic thresholds.
Outputs: ModuleResult containing module-specific Report dataclasses.
Failure semantics: indicator modules fail explicitly on missing required data
or insufficient history.
Market generalization: indicators do not assume venue, symbol format, quote,
settlement, or asset class.
"""

__all__ = []
