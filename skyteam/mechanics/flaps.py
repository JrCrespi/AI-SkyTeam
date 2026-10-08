"""Flaps, Co-Pilot only, in order (MB p.8): R-FLA-01..06. Order is enforced by slot ``requires``."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.enums import SlotKind
from skyteam.core.events import EventType

from . import switches


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    if not switches.activate(ctx, slot_id):
        return
    ctx.state.aero_orange += 1
    ctx.emit(EventType.AERODYNAMICS_CHANGED, f"Orange aerodynamics marker -> {ctx.state.aero_orange}",
             marker="orange", value=ctx.state.aero_orange)


def all_deployed(ctx: RuleContext) -> bool:
    return all(ctx.state.switches.get(s.id, False) for s in ctx.panel.slots_of(SlotKind.FLAPS))
