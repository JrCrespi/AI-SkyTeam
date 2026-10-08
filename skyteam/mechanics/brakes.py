"""Brakes, Pilot only, in order (MB p.9-10): R-BRK-01..07."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.events import EventType

from . import switches


def max_landing_speed(ctx: RuleContext) -> int:
    """Highest speed that still stops the plane: speed must be less than the red marker."""
    thresholds = ctx.constants.brake_thresholds
    return thresholds[min(ctx.state.brakes_deployed, len(thresholds) - 1)]


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    if not switches.activate(ctx, slot_id):
        return
    ctx.state.brakes_deployed += 1
    ctx.emit(EventType.BRAKES_CHANGED,
             f"Brake marker advanced ({ctx.state.brakes_deployed} deployed, max landing speed {max_landing_speed(ctx)})",
             deployed=ctx.state.brakes_deployed)
