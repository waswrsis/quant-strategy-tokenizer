"""Agent-facing API."""

from .api import (
    diff,
    execute,
    explain_ir,
    explain_trace,
    fingerprint,
    kernel_plan,
    lock,
    mutate,
    promote,
    recipe_expand,
    recipes,
    tagspec_get,
    tagspec_verify,
    validate,
    verify,
    vocabulary,
)
from .discover import discover

__all__ = [
    "diff",
    "discover",
    "execute",
    "explain_ir",
    "explain_trace",
    "fingerprint",
    "kernel_plan",
    "lock",
    "mutate",
    "promote",
    "recipe_expand",
    "recipes",
    "tagspec_get",
    "tagspec_verify",
    "validate",
    "verify",
    "vocabulary",
]
