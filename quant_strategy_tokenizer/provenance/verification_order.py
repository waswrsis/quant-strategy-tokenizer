"""Verification-state ordering helpers for provenance TagSpecs."""

from __future__ import annotations

from typing import Literal

from quant_strategy_tokenizer.provenance.spec import VerificationStatus

VerificationState = Literal["unverified", "minimally_attached", "fully_verified"]

_ORDER: dict[VerificationState, int] = {
    "unverified": 0,
    "minimally_attached": 1,
    "fully_verified": 2,
}


def verification_state(status: VerificationStatus) -> VerificationState:
    """Return the strongest verification state represented by a status model."""

    if status.fully_verified:
        return "fully_verified"
    if status.minimally_attached:
        return "minimally_attached"
    return "unverified"


def verification_satisfies(current: VerificationState, required: VerificationState) -> bool:
    """Return whether ``current`` is at least as strong as ``required``."""

    return _ORDER[current] >= _ORDER[required]
