"""Rerolls (MB p.4): R-RER-02/03 and the reroll window (P3)."""

from __future__ import annotations

from skyteam.core.context import RuleContext
from skyteam.core.enums import PLAYERS, DecisionKind, Player
from skyteam.core.events import EventType
from skyteam.core.state import PendingDecision


def spend_token(ctx: RuleContext, player: Player) -> None:
    """Spend a token: BOTH players then choose which hidden dice to reroll, once."""
    state = ctx.state
    state.reroll_supply -= 1
    ctx.emit(EventType.REROLL_USED, f"{player.value} spends a reroll token", player=player.value)
    choices = [PendingDecision(DecisionKind.REROLL_CHOICE, p) for p in PLAYERS if state.hidden_dice(p)]
    state.pending[:0] = choices


def reroll(ctx: RuleContext, player: Player, die_ids: tuple[int, ...]) -> None:
    for die_id in die_ids:
        ctx.state.die(die_id).value = ctx.rng.roll("dice", ctx.constants.die_sides)
    values = [ctx.state.die(i).value for i in die_ids]
    ctx.emit(EventType.DICE_REROLLED, f"{player.value} rerolls {len(die_ids)} dice",
             player=player.value, count=len(die_ids))
    ctx.emit(EventType.DICE_REROLLED, f"{player.value} rerolled to {values}", private_to=player.value,
             player=player.value, die_ids=list(die_ids), values=values)
