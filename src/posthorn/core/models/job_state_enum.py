from __future__ import annotations

from enum import StrEnum, auto


class JobState(StrEnum):
    """
    Represents the lifecycle of a JobPost within the Posthorn state machine.
    """
    DISCOVERED = auto()    # Found by a JobBoard adapter, but not yet evaluated
    DUPLICATE = auto()     # Already existed in the ledger
    ALERT_QUEUED = auto()  # Verified as new, ready for dispatch
    ALERT_SENT = auto()    # Successfully dispatched by an AlertCarrier
    FAILED = auto()        # Carrier failed to dispatch the alert
