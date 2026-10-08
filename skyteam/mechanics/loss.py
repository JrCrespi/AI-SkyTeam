"""Centralised loss checks that are not tied to a single placement.

Immediate losses (axis spin, collision, overshoot) are raised by the mechanic that
causes them. This module covers the checks made at fixed moments of the round.
"""

from __future__ import annotations

from skyteam.core.context import Hook, RuleContext
from skyteam.core.enums import LossReason

from . import altitude, approach


def check_mandatory_slots(ctx: RuleContext) -> None:
    """R-MAND-02 / R-LOSS-04: one die of each colour on the Axis and on the Engines."""
    missing = [s.id for s in ctx.panel.mandatory_slots() if ctx.state.slots.get(s.id) is None]
    if missing:
        ctx.lose(LossReason.MANDATORY_SLOT_EMPTY, f"mandatory spaces left empty: {', '.join(missing)}")


def check_reached_airport_in_time(ctx: RuleContext) -> None:
    """R-END-03 / R-LOSS-05: the Airplane is in the Altitude screen but not the Airport."""
    if altitude.is_final_round(ctx) and not approach.at_airport(ctx):
        ctx.lose(LossReason.CRASH_BEFORE_AIRPORT, "out of altitude before reaching the airport")


def check_game_end(ctx: RuleContext) -> None:
    """Module conditions evaluated at the end of the game (intern, ice brakes)."""
    for fn in ctx.hooks.get(Hook.GAME_END_CHECKS):
        result = fn(ctx)
        if result is not None:
            ctx.lose(*result)
            return
