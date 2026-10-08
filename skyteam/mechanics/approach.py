"""Approach track movement (MB p.6, p.10): R-APP-01..07, R-LOSS-02/03."""

from __future__ import annotations

from skyteam.core.context import Hook, RuleContext
from skyteam.core.enums import LossReason
from skyteam.core.events import EventType


def at_airport(ctx: RuleContext) -> bool:
    return ctx.state.approach_position == ctx.scenario.approach_track.airport_index


def advance(ctx: RuleContext, steps: int) -> None:
    """Move one space at a time; each step checks the Current Position first (R-APP-04).

    TODO_RULE_VERIFICATION P7: step-by-step collision check when advancing 2.
    """
    state = ctx.state
    start = state.approach_position
    for _ in range(steps):
        pos = state.approach_position
        if state.traffic[pos] > 0:
            ctx.lose(LossReason.COLLISION, f"collision with traffic on approach space {pos}")
            return
        if pos == ctx.scenario.approach_track.airport_index:
            ctx.lose(LossReason.OVERSHOOT, "the plane overshot the airport")
            return
        for fn in ctx.hooks.get(Hook.BEFORE_PLANE_STEP):
            fn(ctx, pos)
            if state.is_terminal:
                return
        state.approach_position = pos + 1
        ctx.emit(EventType.PLANE_STEP, f"Plane moves to approach space {pos + 1}",
                 from_index=pos, to_index=pos + 1)
    if steps:
        ctx.emit(EventType.PLANE_ADVANCED, f"Plane advanced {steps} (space {start} -> {state.approach_position})",
                 steps=steps, from_index=start, to_index=state.approach_position)
