"""``RuleContext``: what a mechanic, module or ability receives to read and change the game.

It bundles the mutable ``GameState`` with the immutable configuration (panel, scenario),
the random streams, the event bus and the rule hooks. Mechanics never import ``game.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .enums import GamePhase, GameStatus, LossReason, WinReason
from .events import EventBus, EventType, GameEvent
from .panel import PanelLayout
from .rng import RngStreams
from .state import GameState

if TYPE_CHECKING:
    from skyteam.scenarios.model import Scenario


class Hook:
    """Named extension points. Modules and abilities register callables here.

    Each mechanic documents which points it consults; base game registers none.
    """

    SPEED_MODIFIER = "speed_modifier"          # (ctx, speed) -> int   added to engine speed
    BEFORE_PLANE_STEP = "before_plane_step"    # (ctx, from_index) -> None   may call ctx.lose
    AFTER_AXIS = "after_axis"                  # (ctx) -> None
    AFTER_ENGINES = "after_engines"            # (ctx, speed) -> None
    ROUND_START = "round_start"                # (ctx) -> None   after rerolls are collected
    ROUND_END_FINAL_STEP = "round_end_final"   # (ctx) -> None   "very end" of End of Round
    PLACEMENT_RULES = "placement_rules"        # (ctx, action) -> list[str]   extra violations
    LANDING_CHECKS = "landing_checks"          # (ctx) -> tuple[LossReason, str] | None
    GAME_END_CHECKS = "game_end_checks"        # (ctx) -> tuple[LossReason, str] | None


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable[..., Any]]] = {}

    def register(self, point: str, fn: Callable[..., Any]) -> None:
        self._hooks.setdefault(point, []).append(fn)

    def get(self, point: str) -> list[Callable[..., Any]]:
        return self._hooks.get(point, [])


class RuleContext:
    def __init__(
        self,
        state: GameState,
        panel: PanelLayout,
        scenario: "Scenario",
        bus: EventBus,
        hooks: HookRegistry,
        events: list[GameEvent],
    ) -> None:
        self.state = state
        self.panel = panel
        self.scenario = scenario
        self.bus = bus
        self.hooks = hooks
        self.events = events
        self.rng = RngStreams(state.rng)

    @property
    def constants(self):
        return self.panel.constants

    def emit(self, type_: EventType, text: str, private_to: str | None = None, **data: Any) -> None:
        event = GameEvent(type_, self.state.round, text, data, private_to)
        self.events.append(event)
        self.bus.publish(event)

    def lose(self, reason: LossReason, text: str) -> None:
        """End the game immediately with a loss. Idempotent: the first reason wins."""
        if self.state.is_terminal:
            return
        self.state.status = GameStatus.LOST
        self.state.terminal_reason = reason.value
        self.state.phase = GamePhase.GAME_OVER
        self.state.pending.clear()
        self.emit(EventType.GAME_LOST, f"Game lost: {text}", reason=reason.value)

    def win(self, reason: WinReason, text: str) -> None:
        if self.state.is_terminal:
            return
        self.state.status = GameStatus.WON
        self.state.terminal_reason = reason.value
        self.state.phase = GamePhase.GAME_OVER
        self.emit(EventType.GAME_WON, text, reason=reason.value)
