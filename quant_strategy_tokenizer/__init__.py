"""Quant Strategy Tokenizer public API."""

from .tokens.registry import get_registry

__version__ = "0.1.0"

# Freeze built-in token registry on package import.
get_registry()

from . import agent  # noqa: E402

__all__ = ["agent"]
