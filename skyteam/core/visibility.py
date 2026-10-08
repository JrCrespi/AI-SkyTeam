"""What each player is allowed to know (hidden information).

The only hidden information in the base game is the value of dice still behind a
player's screen (R-GEN-03, R-COM-03). RNG state and the seed are never exposed.
"""

from __future__ import annotations

from typing import Any

from .context import RuleContext
from .enums import Player
from .events import GameEvent
from .state import DISCARDED


def visible_events(events: list[GameEvent], player: Player) -> list[GameEvent]:
    return [e for e in events if e.private_to is None or e.private_to == player.value]


def structured_observation(ctx: RuleContext, player: Player) -> dict[str, Any]:
    s = ctx.state
    own = [{"die_id": d.die_id, "value": d.value} for d in s.hidden_dice(player)]
    placed = [{"die_id": d.die_id, "owner": d.owner.value, "value": d.value, "slot": d.slot}
              for d in s.dice if d.placed and d.slot != DISCARDED]
    return {
        "player": player.value,
        "scenario_id": s.scenario_id,
        "round": s.round,
        "phase": s.phase.value,
        "active_player": s.active_player.value if s.active_player else None,
        "pending": [{"kind": p.kind.value, "player": p.player.value} for p in s.pending],
        "own_hidden_dice": own,
        "partner_hidden_dice_count": len(s.hidden_dice(player.partner)),
        "placed_dice": placed,
        "slots": dict(s.slots),
        "switches": dict(s.switches),
        "axis": s.axis,
        "aero_blue": s.aero_blue,
        "aero_orange": s.aero_orange,
        "brakes_deployed": s.brakes_deployed,
        "coffee": s.coffee,
        "reroll_supply": s.reroll_supply,
        "altitude_index": s.altitude_index,
        "altitude_rerolls": list(s.altitude_rerolls),
        "approach_position": s.approach_position,
        "traffic": list(s.traffic),
        "plane_supply": s.plane_supply,
        "last_speed": s.last_speed,
        "modules": {k: v for k, v in s.modules.items() if not k.startswith("_")},
        "status": s.status.value,
        "terminal_reason": s.terminal_reason,
    }
