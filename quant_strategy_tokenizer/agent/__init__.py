"""Agent-facing API."""

from .api import (
    diff,
    execute,
    explain_ir,
    explain_trace,
    kernel_plan,
    mutate,
    promote,
    recipe_expand,
    recipes,
    tagspec_get,
    tagspec_verify,
    validate,
    vocabulary,
)
from .discover import discover

__all__ = [
    "diff",
    "discover",
    "execute",
    "explain_ir",
    "explain_trace",
    "kernel_plan",
    "mutate",
    "promote",
    "recipe_expand",
    "recipes",
    "tagspec_get",
    "tagspec_verify",
    "validate",
    "vocabulary",
]
