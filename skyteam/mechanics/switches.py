"""Shared handling of switch-based systems (landing gear, flaps, brakes)."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.events import EventType


def activate(ctx: RuleContext, slot_id: str) -> bool:
    """Turn the switch on. Returns False when it was already on (no effect, R-GEA-05).

    TODO_RULE_VERIFICATION P9: the manual only states this for the landing gear; flaps and
    brakes follow the same behaviour until confirmed.
    """
    if ctx.state.switches.get(slot_id, False):
        ctx.emit(EventType.SWITCH_ACTIVATED, f"{slot_id} already active: no effect", slot=slot_id, new=False)
        return False
    ctx.state.switches[slot_id] = True
    ctx.emit(EventType.SWITCH_ACTIVATED, f"{slot_id} activated", slot=slot_id, new=True)
    return True
