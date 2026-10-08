"""Axis (MB p.5): R-AXI-01..06, R-LOSS-01."""

from __future__ import annotations

from skyteam.core.context import Hook, RuleContext
from skyteam.core.enums import LossReason, Player, SlotKind
from skyteam.core.events import EventType


def axis_delta(pilot_value: int, copilot_value: int) -> int:
    """Change of the axis: toward the player with the higher die, by the difference (R-AXI-02).

    Negative values tilt toward the Pilot, positive toward the Co-Pilot.
    """
    return copilot_value - pilot_value


def is_spin(axis: int, spin_at: int) -> bool:
    """R-AXI-04: reaching or passing an X loses the game."""
    return abs(axis) >= spin_at


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    """Resolve as soon as the second Axis die is placed (R-AXI-02)."""
    values = _axis_values(ctx)
    if values is None:
        return
    state = ctx.state
    before = state.axis
    state.axis = before + axis_delta(values[Player.PILOT], values[Player.COPILOT])
    ctx.emit(
        EventType.AXIS_CHANGED,
        f"Axis {before:+d} -> {state.axis:+d} (pilot {values[Player.PILOT]}, copilot {values[Player.COPILOT]})",
        before=before, after=state.axis,
    )
    if is_spin(state.axis, ctx.constants.axis_spin_at):
        ctx.lose(LossReason.AXIS_SPIN, f"axis reached {state.axis:+d}, the plane went into a spin")
        return
    for fn in ctx.hooks.get(Hook.AFTER_AXIS):
        fn(ctx)


def _axis_values(ctx: RuleContext) -> dict[Player, int] | None:
    values: dict[Player, int] = {}
    for slot in ctx.panel.slots_of(SlotKind.AXIS):
        die = ctx.state.die_in(slot.id)
        if die is None:
            return None
        values[die.owner] = die.value
    return values if len(values) == 2 else None
