"""
quant_strategy_tokenizer.pipeline
=========================
Module purpose: run user-selected modules in a deterministic sequence.
Core idea: users should be able to arrange small modules as a pipeline while
preserving each module's standalone Request/Result API.
Inputs: initial payload and a list of callables that accept the previous
payload and return ModuleResult.
Configuration: create `PipelineStep` objects with a step name and callable;
set `continue_on_failure=True` in `run_pipeline` only when exploratory runs
should continue after a failed module.
Outputs: PipelineReport with per-step results and the final payload.
Failure semantics: pipeline stops on the first failed step by default; callers
can opt into continue_on_failure for exploratory analysis.
Market generalization: the pipeline is data-shape agnostic and does not know
about instruments or venues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List

from .contracts import ModuleEvent, ModuleResult


@dataclass
class PipelineStep:
    """One callable module step in a user-defined pipeline.

    Configuration:
    - `name`: human-readable step id used in events and failure reports.
    - `fn`: callable that receives the previous payload and returns
      `ModuleResult`.
    """

    name: str
    fn: Callable[[Any], ModuleResult[Any]]


@dataclass
class PipelineReport:
    final_payload: Any = None
    step_results: List[ModuleResult[Any]] = field(default_factory=list)


def run_pipeline(initial_payload: Any, steps: List[PipelineStep], *, continue_on_failure: bool = False) -> ModuleResult[PipelineReport]:
    payload = initial_payload
    results: List[ModuleResult[Any]] = []
    events: List[ModuleEvent] = []
    for step in steps:
        try:
            res = step.fn(payload)
        except Exception as exc:
            res = ModuleResult.fail(
                "pipeline_step_exception",
                f"pipeline step raised: {step.name}",
                details={"step": step.name, "error": str(exc), "error_type": type(exc).__name__},
            )
        results.append(res)
        events.extend(res.events or [])
        if not res.ok:
            if not continue_on_failure:
                return ModuleResult.fail(
                    "pipeline_step_failed",
                    f"pipeline step failed: {step.name}",
                    details={"step": step.name, "failure": res.failure},
                    events=events,
                )
            continue
        payload = res.value
    return ModuleResult.success(PipelineReport(final_payload=payload, step_results=results), events=events)


__all__ = ["PipelineStep", "PipelineReport", "run_pipeline"]
