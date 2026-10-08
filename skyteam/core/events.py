"""Structured game events.

Every state change worth logging produces a ``GameEvent``. The list of events is the
structured history; ``GameEvent.text`` is the human-readable line. Modules and abilities
subscribe to events through ``EventBus``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    GAME_STARTED = "game_started"
    ROUND_STARTED = "round_started"
    REROLL_GAINED = "reroll_gained"
    STRATEGY_CONFIRMED = "strategy_confirmed"
    DICE_ROLLED = "dice_rolled"
    COFFEE_SPENT = "coffee_spent"
    DIE_PLACED = "die_placed"
    DIE_DISCARDED = "die_discarded"
    REROLL_USED = "reroll_used"
    DICE_REROLLED = "dice_rerolled"
    AXIS_CHANGED = "axis_changed"
    SPEED_RESOLVED = "speed_resolved"
    PLANE_STEP = "plane_step"            # emitted before each one-space move (turns, collisions)
    PLANE_ADVANCED = "plane_advanced"
    TRAFFIC_REMOVED = "traffic_removed"
    TRAFFIC_ADDED = "traffic_added"
    SWITCH_ACTIVATED = "switch_activated"
    AERODYNAMICS_CHANGED = "aerodynamics_changed"
    BRAKES_CHANGED = "brakes_changed"
    COFFEE_GAINED = "coffee_gained"
    ROUND_ENDED = "round_ended"
    ALTITUDE_CHANGED = "altitude_changed"
    LANDING_STARTED = "landing_started"
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"


@dataclass(frozen=True, slots=True)
class GameEvent:
    type: EventType
    round: int
    text: str
    data: dict[str, Any] = field(default_factory=dict)
    private_to: str | None = None   # player value when the event reveals hidden info

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "round": self.round, "text": self.text,
                "data": dict(self.data), "private_to": self.private_to}


Listener = Callable[[GameEvent], None]


class EventBus:
    """Synchronous publish/subscribe. Listeners run in subscription order (deterministic)."""

    def __init__(self) -> None:
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def publish(self, event: GameEvent) -> None:
        for listener in list(self._listeners):
            listener(event)
