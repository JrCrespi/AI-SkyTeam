"""Fixed, player-relative integer encoding of every action.

Dice are addressed by their **value**, not by their identity: two hidden dice showing the same
value are interchangeable, so "place a 5 on the Axis" is one action whichever 5 it is. This keeps
the meaning of each index stable from game to game, which is what lets a network learn it.
Decoding picks the acting player's hidden die with that value (lowest id). Rerolls choose a
subset of the player's hidden dice sorted by (value, id).

The space only depends on the Control Panel layout. Layout for the base panel (20 slots,
6 values, coffee changes -3..+3, 4 dice per player):

    [0]           ConfirmStrategy
    [1, 841)      PlaceDie(value, slot, delta)   1 + (value-1)*140 + slot*7 + (delta+3)
    [841, 847)    DiscardDie(value)
    [847]         UseReroll
    [848]         PassReroll
    [849, 865)    ChooseReroll(bitmask over hidden dice sorted by value)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from skyteam.core.actions import (
    Action,
    ChooseRerollAction,
    ConfirmStrategyAction,
    DiscardDieAction,
    PassRerollAction,
    PlaceDieAction,
    UseRerollAction,
)
from skyteam.core.enums import Player
from skyteam.core.panel import PanelLayout
from skyteam.core.state import DieState, GameState


def sorted_hidden_dice(state: GameState, player: Player) -> list[DieState]:
    return sorted(state.hidden_dice(player), key=lambda d: (d.value or 0, d.die_id))


@dataclass(frozen=True)
class ActionSpace:
    panel: PanelLayout
    _slot_idx: dict[str, int] = field(init=False, repr=False, compare=False)
    dice: int = field(init=False, compare=False)
    sides: int = field(init=False, compare=False)
    max_delta: int = field(init=False, compare=False)
    n_deltas: int = field(init=False, compare=False)
    n_slots: int = field(init=False, compare=False)
    place_offset: int = field(init=False, compare=False)
    discard_offset: int = field(init=False, compare=False)
    use_reroll_index: int = field(init=False, compare=False)
    pass_reroll_index: int = field(init=False, compare=False)
    choose_offset: int = field(init=False, compare=False)
    size: int = field(init=False, compare=False)

    def __post_init__(self) -> None:
        c = self.panel.constants
        dice, sides = c.dice_per_player, c.die_sides
        max_delta = min(c.coffee_max, c.coffee_max_per_die)
        n_deltas = 2 * max_delta + 1
        n_slots = len(self.panel.slots)
        place_offset = 1
        discard_offset = place_offset + sides * n_slots * n_deltas
        use_reroll_index = discard_offset + sides
        values = {
            "_slot_idx": {s.id: i for i, s in enumerate(self.panel.slots)},
            "dice": dice, "sides": sides, "max_delta": max_delta, "n_deltas": n_deltas, "n_slots": n_slots,
            "place_offset": place_offset, "discard_offset": discard_offset,
            "use_reroll_index": use_reroll_index, "pass_reroll_index": use_reroll_index + 1,
            "choose_offset": use_reroll_index + 2, "size": use_reroll_index + 2 + 2 ** dice,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    # ------------------------------------------------------------------ encode / decode
    def encode(self, action: Action, state: GameState) -> int:
        if isinstance(action, ConfirmStrategyAction):
            return 0
        if isinstance(action, PlaceDieAction):
            value = state.die(action.die_id).value
            return (self.place_offset + (value - 1) * self.n_slots * self.n_deltas
                    + self._slot_idx[action.slot_id] * self.n_deltas + action.coffee_delta + self.max_delta)
        if isinstance(action, DiscardDieAction):
            return self.discard_offset + state.die(action.die_id).value - 1
        if isinstance(action, UseRerollAction):
            return self.use_reroll_index
        if isinstance(action, PassRerollAction):
            return self.pass_reroll_index
        if isinstance(action, ChooseRerollAction):
            order = [d.die_id for d in sorted_hidden_dice(state, action.player)]
            return self.choose_offset + sum(1 << order.index(d) for d in action.die_ids)
        raise ValueError(f"action type {type(action).__name__} has no encoding")

    def decode(self, index: int, player: Player, state: GameState) -> Action:
        """The action for ``index`` in ``state``. Indices naming a die the player lacks raise ValueError."""
        if not 0 <= index < self.size:
            raise ValueError(f"action index {index} outside [0, {self.size})")
        if index == 0:
            return ConfirmStrategyAction(player)
        if index < self.discard_offset:
            value, rest = divmod(index - self.place_offset, self.n_slots * self.n_deltas)
            slot, delta = divmod(rest, self.n_deltas)
            return PlaceDieAction(player, self._die_with_value(state, player, value + 1),
                                  self.panel.slots[slot].id, delta - self.max_delta)
        if index < self.use_reroll_index:
            return DiscardDieAction(player, self._die_with_value(state, player, index - self.discard_offset + 1))
        if index == self.use_reroll_index:
            return UseRerollAction(player)
        if index == self.pass_reroll_index:
            return PassRerollAction(player)
        mask = index - self.choose_offset
        order = sorted_hidden_dice(state, player)
        if mask >> len(order):
            raise ValueError(f"reroll mask {mask:b} names more dice than the {len(order)} hidden")
        return ChooseRerollAction(player, tuple(sorted(order[i].die_id for i in range(len(order)) if mask >> i & 1)))

    @staticmethod
    def _die_with_value(state: GameState, player: Player, value: int) -> int:
        for die in sorted_hidden_dice(state, player):
            if die.value == value:
                return die.die_id
        raise ValueError(f"the {player.value} has no hidden die showing {value}")
