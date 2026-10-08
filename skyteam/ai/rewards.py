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


class RoundSurvivedReward:
    """Shaping term: 1 each time a round ends without losing.

    Used with a small weight so the agent first learns to finish rounds (fill the mandatory
    spaces, keep the axis level) before it ever sees a landing. The terminal reward still
    dominates: 7 rounds at weight 0.05 are worth 0.35, a landing is worth 1.
    """

    uses_before = True

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        if before is None or after.status is GameStatus.LOST:
            return 0.0
        return 1.0 if after.round > before.round or (after.status is GameStatus.WON) else 0.0


class ApproachProgressReward:
    """Shaping term: fraction of the approach track covered by this action (1.0 = start to airport)."""

    uses_before = True

    def __init__(self, track_length: int) -> None:
        self.track_length = max(1, track_length)

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        if before is None or after.status is GameStatus.LOST:
            return 0.0
        return (after.approach_position - before.approach_position) / self.track_length


class LandingConfigReward:
    """Shaping term: 1 per Landing Gear, Flaps or Brakes switch activated by this action.

    Gear and Flaps must all be deployed to land; Brakes are what lets the landing speed pass.
    """

    uses_before = True
    PREFIXES = ("gear.", "flaps.", "brakes.")

    def _count(self, state: GameState) -> int:
        return sum(1 for k, on in state.switches.items() if on and k.startswith(self.PREFIXES))

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        if before is None or after.status is GameStatus.LOST:
            return 0.0
        return float(self._count(after) - self._count(before))


class TrafficClearedReward:
    """Shaping term: 1 per airplane removed from the approach track (all must be gone to land)."""

    uses_before = True

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        if before is None or after.status is GameStatus.LOST:
            return 0.0
        return float(max(0, sum(before.traffic) - sum(after.traffic)))


class LandingConditionsReward:
    """Shaping term at the end of the landing round: 1 per landing condition met (A to D, MB p.11).

    Gives a signal for a nearly successful landing, which the outcome alone does not.
    """

    uses_before = False
    CONFIG = ("gear.", "flaps.")

    def __call__(self, before: GameState | None, action: Action, after: GameState) -> float:
        landed_or_tried = after.status is GameStatus.WON or str(after.terminal_reason or "").startswith("landing_")
        if not after.is_terminal or not landed_or_tried:
            return 0.0
        config = [on for k, on in after.switches.items() if k.startswith(self.CONFIG)]
        return float((sum(after.traffic) == 0) + all(config) + (after.axis == 0) + bool(after.landing_speed_ok))


def training_reward(round_bonus: float = 0.2, progress_bonus: float = 1.0, config_bonus: float = 0.05,
                    traffic_bonus: float = 0.05, landing_bonus: float = 0.25,
                    track_length: int = 6) -> CompositeReward:
    """Default reward for training: the sparse outcome plus shaping terms.

    Shaping only speeds up learning: it pays for surviving rounds, advancing, deploying the
    landing configuration, clearing traffic and meeting each landing condition. A landing adds
    1 and any loss costs 1, so the most a game can give is still to land.
    """
    return CompositeReward((1.0, SparseReward()), (round_bonus, RoundSurvivedReward()),
                           (progress_bonus, ApproachProgressReward(track_length)),
                           (config_bonus, LandingConfigReward()),
                           (traffic_bonus, TrafficClearedReward()),
                           (landing_bonus, LandingConditionsReward()))
