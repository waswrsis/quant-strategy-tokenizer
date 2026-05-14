"""Local adapter discovery foundation."""

from .discovery import ADAPTER_ENTRY_POINT_GROUP, AdapterDescriptor, discover_adapters
from .loader import get_adapter

__all__ = [
    "ADAPTER_ENTRY_POINT_GROUP",
    "AdapterDescriptor",
    "discover_adapters",
    "get_adapter",
]
