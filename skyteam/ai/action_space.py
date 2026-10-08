"""Fixed, player-relative integer encoding of every action.

The space only depends on the Control Panel layout, so it is identical in every state of
every scenario that uses the same panel. Dice are addressed by their *ordinal* among the
acting player's dice (0..3), so the same index means the same thing for both roles.

Layout (base panel, 20 slots, 4 dice, coffee deltas -3..+3):

    [0]                    ConfirmStrategy
    [1, 1+560)             PlaceDie(ordinal, slot, delta)   ordinal*140 + slot*7 + (delta+3)
    [561, 565)             DiscardDie(ordinal)
    [565]                  UseReroll
    [566]                  PassReroll
    [567, 583)             ChooseReroll(bitmask of ordinals)
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


@dataclass(frozen=True)
class ActionSpace:
    panel: PanelLayout
    _slot_idx: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_slot_idx", {s.id: i for i, s in enumerate(self.panel.slots)})

    @property
    def dice(self) -> int:
        return self.panel.constants.dice_per_player

    @property
    def max_delta(self) -> int:
        return min(self.panel.constants.coffee_max, self.panel.constants.coffee_max_per_die)

    @property
    def n_deltas(self) -> int:
        return 2 * self.max_delta + 1

    @property
    def n_slots(self) -> int:
        return len(self.panel.slots)

    # block offsets
    @property
    def place_offset(self) -> int:
        return 1

    @property
    def discard_offset(self) -> int:
        return self.place_offset + self.dice * self.n_slots * self.n_deltas

    @property
    def use_reroll_index(self) -> int:
        return self.discard_offset + self.dice

    @property
    def pass_reroll_index(self) -> int:
        return self.use_reroll_index + 1

    @property
    def choose_offset(self) -> int:
        return self.pass_reroll_index + 1

    @property
    def size(self) -> int:
        return self.choose_offset + 2 ** self.dice

    # ------------------------------------------------------------------ helpers
    def _die_offset(self, player: Player) -> int:
        return 0 if player is Player.PILOT else self.dice

    def _slot_index(self, slot_id: str) -> int:
        return self._slot_idx[slot_id]

    # ------------------------------------------------------------------ encode / decode
    def encode(self, action: Action) -> int:
        p = action.player
        if isinstance(action, ConfirmStrategyAction):
            return 0
        if isinstance(action, PlaceDieAction):
            ordinal = action.die_id - self._die_offset(p)
            return (self.place_offset + ordinal * self.n_slots * self.n_deltas
                    + self._slot_index(action.slot_id) * self.n_deltas + action.coffee_delta + self.max_delta)
        if isinstance(action, DiscardDieAction):
            return self.discard_offset + action.die_id - self._die_offset(p)
        if isinstance(action, UseRerollAction):
            return self.use_reroll_index
        if isinstance(action, PassRerollAction):
            return self.pass_reroll_index
        if isinstance(action, ChooseRerollAction):
            mask = sum(1 << (d - self._die_offset(p)) for d in action.die_ids)
            return self.choose_offset + mask
        raise ValueError(f"action type {type(action).__name__} has no encoding")

    def decode(self, index: int, player: Player) -> Action:
        if not 0 <= index < self.size:
            raise ValueError(f"action index {index} outside [0, {self.size})")
        off = self._die_offset(player)
        if index == 0:
            return ConfirmStrategyAction(player)
        if index < self.discard_offset:
            rest = index - self.place_offset
            ordinal, rest = divmod(rest, self.n_slots * self.n_deltas)
            slot, delta = divmod(rest, self.n_deltas)
            return PlaceDieAction(player, off + ordinal, self.panel.slots[slot].id, delta - self.max_delta)
        if index < self.use_reroll_index:
            return DiscardDieAction(player, off + index - self.discard_offset)
        if index == self.use_reroll_index:
            return UseRerollAction(player)
        if index == self.pass_reroll_index:
            return PassRerollAction(player)
        mask = index - self.choose_offset
        return ChooseRerollAction(player, tuple(off + i for i in range(self.dice) if mask >> i & 1))
