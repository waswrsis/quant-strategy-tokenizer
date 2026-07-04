"""QST 1.0 read-only evidence collection."""

from qst.collectors.protocol import (
    ALLOWED_TRANSITIONS,
    EvidenceAdapter,
    transition_activity,
    verified_result_evidence,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "EvidenceAdapter",
    "transition_activity",
    "verified_result_evidence",
]

