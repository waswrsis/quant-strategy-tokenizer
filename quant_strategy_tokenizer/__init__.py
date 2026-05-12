"""
quant_strategy_tokenizer
========================
Module purpose: public package surface for Quant Strategy Tokenizer.
Core idea: Expose package identity without importing heavy modules or triggering side effects. Assumes users will import concrete tokens directly from their module paths when they need computation.
Inputs: normal Python imports only.
Outputs: package metadata and importable submodules.
Failure semantics: import should not validate data, load credentials, create exchanges, or write files.
Market generalization: package initialization is independent of asset class, venue, and data source.
"""
from .contracts import (
    DataFrameSpec,
    DetailLevel,
    ExtractorSpec,
    InstrumentRef,
    ModuleEvent,
    ModuleFailure,
    ModuleResult,
    ModuleRunContext,
    OutputFiles,
)

__all__ = [
    "DataFrameSpec",
    "DetailLevel",
    "ExtractorSpec",
    "InstrumentRef",
    "ModuleEvent",
    "ModuleFailure",
    "ModuleResult",
    "ModuleRunContext",
    "OutputFiles",
]
