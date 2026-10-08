"""Altitude track and end of round (MB p.4, p.9-10): R-ALT-*, R-END-*, R-RER-01."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.events import EventType


def current_space(ctx: RuleContext):
    return ctx.scenario.altitude_track.spaces[ctx.state.altitude_index]


def is_final_round(ctx: RuleContext) -> bool:
    """The Airplane image is in the Current Altitude screen (R-LND-00)."""
    return current_space(ctx).final


def collect_reroll(ctx: RuleContext) -> None:
    """R-RER-01: a Reroll token on the Current Altitude space goes to the supply."""
    state = ctx.state
    if state.altitude_rerolls[state.altitude_index]:
        state.altitude_rerolls[state.altitude_index] = False
        state.reroll_supply += 1
        ctx.emit(EventType.REROLL_GAINED, f"Reroll token collected ({state.reroll_supply} in supply)",
                 supply=state.reroll_supply)


def descend(ctx: RuleContext) -> None:
    """R-END-01 step 1: advance the Altitude Track one space."""
    state = ctx.state
    state.altitude_index += 1
    space = current_space(ctx)
    label = "landing" if space.final else f"{space.altitude} ft"
    ctx.emit(EventType.ALTITUDE_CHANGED, f"Altitude -> {label}", altitude=space.altitude,
             index=state.altitude_index)
