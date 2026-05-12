"""
quant_strategy_tokenizer.data_schema
====================================
Module purpose: standalone tabular data-schema validation token.
Core idea: Run the same normalization path that indicators use, then return field mappings, row profile, and schema diagnostics. Assumes callers may want to validate raw vendor data before passing it into a strategy module.
Inputs: raw tabular data, required fields, optional fields, DataFrameSpec, ExtractorSpec, and ModuleRunContext.
Outputs: DataSchemaReport with row count, resolved fields, missing fields, input profile, warnings, and optional files.
Failure semantics: missing required fields, invalid timestamps, invalid numeric fields, empty input, and unsupported input return ModuleResult.fail.
Market generalization: schema validation is field-based and does not assume symbols, sessions, venues, or asset class.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contracts import DataFrameSpec, ExtractorSpec, ModuleEvent, ModuleResult, ModuleRunContext
from .normalization import normalize_frame
from .reporting import write_module_report


@dataclass
class DataSchemaParams:
    """Fields the caller wants the raw data checked against.

    Configuration:
    - `required_fields`: logical field names that must resolve through
      `DataFrameSpec` or aliases; missing fields fail the module.
    - `optional_fields`: logical fields to report if present; missing fields
      are listed but do not fail validation.
    """

    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)


@dataclass
class DataSchemaRequest:
    data: Any
    params: DataSchemaParams = field(default_factory=DataSchemaParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="data_schema"))


@dataclass
class DataSchemaReport:
    quality: str
    rows: int
    used_fields: Dict[str, str]
    missing_fields: List[str]
    optional_missing_fields: List[str]
    input_profile: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def run(request: DataSchemaRequest) -> ModuleResult[DataSchemaReport]:
    norm = normalize_frame(
        request.data,
        required_fields=request.params.required_fields,
        optional_fields=request.params.optional_fields,
        spec=request.spec,
        extractor=request.extractor,
    )
    if not norm.ok:
        return ModuleResult.fail(norm.failure.kind, norm.failure.message, field=norm.failure.field, details=norm.failure.details)
    nf = norm.value
    if nf is None:
        return ModuleResult.fail("internal_error", "normalization returned no frame")
    report = DataSchemaReport(
        quality="ok",
        rows=int(len(nf.frame)),
        used_fields=nf.used_fields,
        missing_fields=nf.missing_fields,
        optional_missing_fields=nf.optional_missing_fields,
        input_profile=nf.input_profile,
        warnings=nf.warnings,
        diagnostics={"required_fields": request.params.required_fields, "optional_fields": request.params.optional_fields},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="data_schema.validated", fields={"rows": report.rows})], warnings=nf.warnings)
    if request.context.output_dir:
        result.files = write_module_report("data_schema", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["DataSchemaParams", "DataSchemaRequest", "DataSchemaReport", "run"]
