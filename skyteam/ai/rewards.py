"""Reward functions. The engine never computes rewards; it only reports the outcome.

Sky Team is cooperative: both players receive the same reward.
"""

from __future__ import annotations

from typing import Protocol

from skyteam.core.actions import Action
from skyteam.core.enums import GameStatus
from skyteam.core.state import GameState


class RewardFn(Protocol):
    """``before`` is a copy of the state before the action, or None when ``uses_before`` is False."""

    uses_before: bool

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float: ...


class SparseReward:
    """+1 for a landing, -1 for any loss, 0 otherwise."""

    uses_before = False

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        if after.status is GameStatus.WON:
            return 1.0
        if after.status is GameStatus.LOST:
            return -1.0
        return 0.0


class CompositeReward:
    """Sum of weighted reward terms, so auxiliary shaping can be added without touching the engine."""

    def __init__(self, *terms: tuple[float, RewardFn]) -> None:
        self.terms = terms
        self.uses_before = any(getattr(fn, "uses_before", True) for _, fn in terms)

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        return sum(weight * fn(before, action, after) for weight, fn in self.terms)
