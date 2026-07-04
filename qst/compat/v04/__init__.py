"""Legacy qst-ir/0.4 and custom-runtime compatibility exports."""

from qst.custom_runtime import (
    ApprovalRequest,
    ApprovalStore,
    TokenRuntimeContext,
    TokenRuntimeService,
    load_token_pack,
)
from qst.hash import compute_hashes_v2
from qst.ir import (
    StrategyIRV04,
    TokenRefV04,
    canonical_bytes_v04,
    load_ir_v04_file,
    validate_ir_v04,
)

__all__ = [
    "ApprovalRequest",
    "ApprovalStore",
    "StrategyIRV04",
    "TokenRefV04",
    "TokenRuntimeContext",
    "TokenRuntimeService",
    "canonical_bytes_v04",
    "compute_hashes_v2",
    "load_ir_v04_file",
    "load_token_pack",
    "validate_ir_v04",
]
