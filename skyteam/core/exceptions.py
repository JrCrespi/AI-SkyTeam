"""Engine exceptions."""

from __future__ import annotations


class SkyTeamError(Exception):
    """Base class for every engine error."""


class IllegalActionError(SkyTeamError):
    """Raised by ``step`` when the action is not legal in the current state."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


class InvalidStateError(SkyTeamError):
    """Raised by ``validate_state`` (strict mode) when an invariant is broken."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class DataError(SkyTeamError):
    """Raised when a data file (panel, track, scenario) is malformed."""
