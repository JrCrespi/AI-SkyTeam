"""Landing Gear, Pilot only (MB p.7): R-GEA-01..06."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.enums import SlotKind
from skyteam.core.events import EventType

from . import switches


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    if not switches.activate(ctx, slot_id):
        return
    ctx.state.aero_blue += 1
    ctx.emit(EventType.AERODYNAMICS_CHANGED, f"Blue aerodynamics marker -> {ctx.state.aero_blue}",
             marker="blue", value=ctx.state.aero_blue)


def all_deployed(ctx: RuleContext) -> bool:
    return all(ctx.state.switches.get(s.id, False) for s in ctx.panel.slots_of(SlotKind.LANDING_GEAR))
