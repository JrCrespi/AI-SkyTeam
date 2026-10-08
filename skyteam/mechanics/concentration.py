"""Concentration and Coffee (MB p.8): R-COF-01..08."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.events import EventType


def coffee_change_allowed(value: int, delta: int, coffee: int, max_per_die: int, sides: int) -> bool:
    """R-COF-03/06: each token is +-1; the result must stay within 1..sides; enough tokens needed."""
    spent = abs(delta)
    return spent <= coffee and spent <= max_per_die and 1 <= value + delta <= sides


def spend(ctx: RuleContext, delta: int) -> None:
    if delta == 0:
        return
    ctx.state.coffee -= abs(delta)
    ctx.emit(EventType.COFFEE_SPENT, f"{abs(delta)} coffee spent ({delta:+d})", delta=delta)


def on_placed(ctx: RuleContext, slot_id: str, value: int) -> None:
    """R-COF-02. With the maximum reached the die is still placed, without a token.

    TODO_RULE_VERIFICATION P4.
    """
    if ctx.state.coffee >= ctx.constants.coffee_max:
        ctx.emit(EventType.COFFEE_GAINED, "Coffee already at maximum: no token gained", gained=0)
        return
    ctx.state.coffee += 1
    ctx.emit(EventType.COFFEE_GAINED, f"Coffee token gained ({ctx.state.coffee})", gained=1)
