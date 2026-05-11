"""
Quant Strategy Tokenizer
========================
Module purpose: fine-grained, reusable strategy building blocks.
Core idea: every module is independently callable, accepts raw or lightly
processed user-supplied data, normalizes it locally, and returns detailed
diagnostics without fetching market data or touching broker state.
Inputs: module-specific Request dataclasses built from raw data, params,
optional extractors, and optional output directories.
Configuration: configure each module through its Request dataclass. Use
`DataFrameSpec` for column names and validation, `ExtractorSpec` for custom raw
objects, module-specific `*Params` for policy, and `ModuleRunContext` for
detail level/report output.
Outputs: ModuleResult objects and optional JSON/JSONL report files.
Failure semantics: invalid or missing inputs produce explicit ModuleFailure;
modules do not fail open.
Market generalization: modules avoid exchange, venue, quote, settlement, and
asset-class assumptions. Instrument metadata is optional and user supplied.

Package note: the project name is Quant Strategy Tokenizer (QST). The formal
Python import path is `quant_strategy_tokenizer`.
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
