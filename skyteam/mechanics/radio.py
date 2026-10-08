"""Radio (MB p.7): R-RAD-01..04."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.events import EventType


def target_space(position: int, value: int) -> int:
    """Count spaces starting with the Current Position (1 = Current Position)."""
    return position + value - 1


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    state = ctx.state
    target = target_space(state.approach_position, value)
    if target >= len(state.traffic) or state.traffic[target] == 0:
        ctx.emit(EventType.TRAFFIC_REMOVED, f"Radio {value}: no airplane on space {target}, no effect",
                 space=target, removed=0)
        return
    state.traffic[target] -= 1
    state.plane_supply += 1
    ctx.emit(EventType.TRAFFIC_REMOVED, f"Radio {value}: airplane removed from space {target}",
             space=target, removed=1)
