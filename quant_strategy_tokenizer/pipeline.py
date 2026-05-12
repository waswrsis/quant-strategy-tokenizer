"""
quant_strategy_tokenizer.pipeline
=========================
Module purpose: run user-selected modules in a deterministic sequence.
Core idea: preserve each module's standalone Request/Result API while giving
the pipeline a small data bus. Steps can read the initial payload, current
payload, prior step outputs, or the whole PipelineState for fan-in.
Inputs: initial payload and PipelineStep definitions. A step callable receives
the selected input and returns ModuleResult.
Configuration: `input_key` selects input from state, `take` selects a field from
the successful report for downstream use, `output_key` stores that selected
payload under a reusable name, and `pass_state=True` passes the full state.
Outputs: PipelineReport with per-step results, named values, and final payload.
Failure semantics: missing inputs, missing selected fields, exceptions, or
failed modules return explicit ModuleResult.fail. The pipeline stops on the
first failed step unless continue_on_failure=True.
Market generalization: the pipeline is data-shape agnostic and does not know
about instruments or venues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .contracts import ModuleEvent, ModuleResult


class PipelineLookupError(KeyError):
    """Raised when a pipeline key/path cannot be resolved from state."""


@dataclass
class PipelineState:
    """Shared data bus for composed module workflows.

    Configuration:
    - `initial_payload`: immutable caller-supplied starting object.
    - `current_payload`: current downstream payload after successful steps.
    - `values`: named successful report values and selected outputs.
    - `results`: full ModuleResult objects keyed by step name.

    Path lookup:
    - `initial` returns the starting payload.
    - `current` returns the current payload.
    - `results.<step>` returns a full ModuleResult.
    - `<step>` returns that step's full report value.
    - `<name>.<field>` walks dict keys or object attributes.
    """

    initial_payload: Any
    current_payload: Any
    values: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, ModuleResult[Any]] = field(default_factory=dict)

    def get(self, key: Optional[str]) -> Any:
        if key is None or key == "" or key == "current":
            return self.current_payload
        if key == "initial":
            return self.initial_payload
        parts = str(key).split(".")
        if parts[0] == "results":
            if len(parts) == 1:
                return self.results
            if parts[1] not in self.results:
                raise PipelineLookupError(f"unknown pipeline result: {parts[1]}")
            value: Any = self.results[parts[1]]
            parts = parts[2:]
        elif parts[0] in self.values:
            value = self.values[parts[0]]
            parts = parts[1:]
        else:
            raise PipelineLookupError(f"unknown pipeline value: {parts[0]}")
        for part in parts:
            value = _get_part(value, part)
        return value

    def set_value(self, key: str, value: Any) -> None:
        if not key:
            raise PipelineLookupError("empty pipeline output key")
        self.values[str(key)] = value


@dataclass
class PipelineStep:
    """One callable module step in a user-defined pipeline.

    Configuration:
    - `name`: human-readable step id used in events and failure reports.
    - `fn`: callable that receives selected input and returns `ModuleResult`.
    - `input_key`: optional state path to feed into `fn`; defaults to current.
    - `take`: optional path selected from `res.value` after success; this is
      what becomes current and what `output_key` stores.
    - `output_key`: optional state name for the selected downstream payload.
    - `pass_state`: when True, `fn` receives PipelineState rather than a single
      selected payload. Use this for fan-in across multiple prior outputs.
    """

    name: str
    fn: Callable[[Any], ModuleResult[Any]]
    input_key: Optional[str] = None
    take: Optional[str] = None
    output_key: Optional[str] = None
    pass_state: bool = False


@dataclass
class PipelineReport:
    final_payload: Any = None
    step_results: List[ModuleResult[Any]] = field(default_factory=list)
    values: Dict[str, Any] = field(default_factory=dict)
    results_by_step: Dict[str, ModuleResult[Any]] = field(default_factory=dict)


def run_pipeline(initial_payload: Any, steps: List[PipelineStep], *, continue_on_failure: bool = False) -> ModuleResult[PipelineReport]:
    state = PipelineState(initial_payload=initial_payload, current_payload=initial_payload, values={"initial": initial_payload})
    results: List[ModuleResult[Any]] = []
    events: List[ModuleEvent] = []
    seen_names: set[str] = set()
    for step in steps:
        if not step.name:
            return ModuleResult.fail("pipeline_invalid_step", "pipeline step name is required", events=events)
        if step.name in seen_names:
            return ModuleResult.fail("pipeline_invalid_step", "pipeline step names must be unique", details={"step": step.name}, events=events)
        seen_names.add(step.name)
        try:
            step_input = state if step.pass_state else state.get(step.input_key)
        except PipelineLookupError as exc:
            res = ModuleResult.fail(
                "pipeline_input_missing",
                f"pipeline input not found for step: {step.name}",
                details={"step": step.name, "input_key": step.input_key or "current", "error": str(exc)},
            )
            results.append(res)
            events.extend(res.events or [])
            if not continue_on_failure:
                return _pipeline_failed(step, res, results, events, state)
            continue
        try:
            res = step.fn(step_input)
        except Exception as exc:
            res = ModuleResult.fail(
                "pipeline_step_exception",
                f"pipeline step raised: {step.name}",
                details={"step": step.name, "error": str(exc), "error_type": type(exc).__name__},
            )
        results.append(res)
        state.results[step.name] = res
        events.extend(res.events or [])
        if not res.ok:
            if not continue_on_failure:
                return _pipeline_failed(step, res, results, events, state)
            continue
        state.values[step.name] = res.value
        try:
            selected = _resolve_relative(res.value, step.take)
        except PipelineLookupError as exc:
            res = ModuleResult.fail(
                "pipeline_output_missing",
                f"pipeline output selection failed for step: {step.name}",
                details={"step": step.name, "take": step.take, "error": str(exc)},
            )
            results[-1] = res
            state.results[step.name] = res
            if not continue_on_failure:
                return _pipeline_failed(step, res, results, events, state)
            continue
        if step.output_key:
            state.set_value(step.output_key, selected)
        state.current_payload = selected
    report = PipelineReport(
        final_payload=state.current_payload,
        step_results=results,
        values=dict(state.values),
        results_by_step=dict(state.results),
    )
    return ModuleResult.success(report, events=events)


def _get_part(value: Any, part: str) -> Any:
    if isinstance(value, dict):
        if part not in value:
            raise PipelineLookupError(f"missing dict key: {part}")
        return value[part]
    if isinstance(value, (list, tuple)) and part.isdigit():
        idx = int(part)
        try:
            return value[idx]
        except IndexError as exc:
            raise PipelineLookupError(f"list index out of range: {part}") from exc
    if hasattr(value, part):
        return getattr(value, part)
    raise PipelineLookupError(f"missing attribute/key: {part}")


def _resolve_relative(value: Any, path: Optional[str]) -> Any:
    if not path:
        return value
    out = value
    for part in str(path).split("."):
        out = _get_part(out, part)
    return out


def _pipeline_failed(
    step: PipelineStep,
    res: ModuleResult[Any],
    results: List[ModuleResult[Any]],
    events: List[ModuleEvent],
    state: PipelineState,
) -> ModuleResult[PipelineReport]:
    return ModuleResult.fail(
        "pipeline_step_failed",
        f"pipeline step failed: {step.name}",
        details={
            "step": step.name,
            "failure": res.failure,
            "completed_steps": list(state.results.keys()),
            "available_values": list(state.values.keys()),
        },
        events=events,
    )


__all__ = ["PipelineLookupError", "PipelineState", "PipelineStep", "PipelineReport", "run_pipeline"]
