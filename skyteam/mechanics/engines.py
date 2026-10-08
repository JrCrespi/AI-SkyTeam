"""Engines (MB p.6, p.10): R-ENG-01..05, R-BRK-07."""

from __future__ import annotations

from skyteam.core.context import Hook, RuleContext
from skyteam.core.enums import SlotKind
from skyteam.core.events import EventType

from . import altitude, approach, brakes


def advance_for_speed(speed: int, aero_blue: int, aero_orange: int) -> int:
    """R-ENG-03. Markers sit between N and N+1 and are stored as N, so there are no ties."""
    if speed <= aero_blue:
        return 0
    if speed <= aero_orange:
        return 1
    return 2


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    dice_values = [ctx.state.die_in(s.id) for s in ctx.panel.slots_of(SlotKind.ENGINES)]
    if any(d is None for d in dice_values):
        return
    base = sum(d.value for d in dice_values)
    speed = base + sum(fn(ctx, base) for fn in ctx.hooks.get(Hook.SPEED_MODIFIER))
    state = ctx.state
    state.last_speed = speed

    if altitude.is_final_round(ctx):
        limit = brakes.max_landing_speed(ctx)
        state.landing_speed_ok = speed <= limit
        ctx.emit(EventType.SPEED_RESOLVED,
                 f"Landing speed {speed} vs brakes (must be <= {limit}): "
                 f"{'OK' if state.landing_speed_ok else 'too fast'}",
                 speed=speed, brake_limit=limit, final=True)
    else:
        steps = advance_for_speed(speed, state.aero_blue, state.aero_orange)
        ctx.emit(EventType.SPEED_RESOLVED,
                 f"Speed {speed} (aero {state.aero_blue}|{state.aero_orange}) -> advance {steps}",
                 speed=speed, steps=steps, final=False)
        approach.advance(ctx, steps)
    if state.is_terminal:
        return
    for fn in ctx.hooks.get(Hook.AFTER_ENGINES):
        fn(ctx, speed)
