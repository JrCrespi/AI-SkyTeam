"""Player actions.

Every action is an immutable value object carrying the acting player. Actions are
serialisable (``to_dict``/``action_from_dict``) so a game can be replayed from
``(scenario, seed, actions)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from .enums import Player


@dataclass(frozen=True, slots=True)
class Action:
    player: Player
    kind: ClassVar[str] = "action"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "player": self.player.value}

    def describe(self) -> str:
        return f"{self.player.value} {self.kind}"


@dataclass(frozen=True, slots=True)
class ConfirmStrategyAction(Action):
    """End of the briefing for this player (R-COM-01). The engine does not model talk."""

    kind: ClassVar[str] = "confirm_strategy"


@dataclass(frozen=True, slots=True)
class PlaceDieAction(Action):
    """Place one hidden die on a free slot, optionally spending Coffee (R-TURN-03, R-COF-03).

    ``coffee_delta`` is the total change applied to the die: each Coffee token spent
    adds or subtracts 1, so ``abs(coffee_delta)`` tokens are spent.
    """

    die_id: int
    slot_id: str
    coffee_delta: int = 0
    kind: ClassVar[str] = "place_die"

    def to_dict(self) -> dict[str, Any]:
        return {**Action.to_dict(self), "die_id": self.die_id, "slot_id": self.slot_id,
                "coffee_delta": self.coffee_delta}

    def describe(self) -> str:
        coffee = f" (coffee {self.coffee_delta:+d})" if self.coffee_delta else ""
        return f"{self.player.value} places die {self.die_id} on {self.slot_id}{coffee}"


@dataclass(frozen=True, slots=True)
class DiscardDieAction(Action):
    """Only legal when the player has no legal placement at all (P2, TODO_RULE_VERIFICATION)."""

    die_id: int
    kind: ClassVar[str] = "discard_die"

    def to_dict(self) -> dict[str, Any]:
        return {**Action.to_dict(self), "die_id": self.die_id}


@dataclass(frozen=True, slots=True)
class UseRerollAction(Action):
    """Spend a Reroll token (R-RER-02)."""

    kind: ClassVar[str] = "use_reroll"


@dataclass(frozen=True, slots=True)
class PassRerollAction(Action):
    """Decline the reroll window offered to the non-active player (P3)."""

    kind: ClassVar[str] = "pass_reroll"


@dataclass(frozen=True, slots=True)
class ChooseRerollAction(Action):
    """Pick which hidden dice to reroll after a token was spent (R-RER-03). May be empty."""

    die_ids: tuple[int, ...] = ()
    kind: ClassVar[str] = "choose_reroll"

    def to_dict(self) -> dict[str, Any]:
        return {**Action.to_dict(self), "die_ids": list(self.die_ids)}


_ACTION_TYPES: dict[str, type[Action]] = {
    cls.kind: cls
    for cls in (ConfirmStrategyAction, PlaceDieAction, DiscardDieAction, UseRerollAction,
                PassRerollAction, ChooseRerollAction)
}


def register_action_type(cls: type[Action]) -> type[Action]:
    """Let modules and abilities add their own action types (usable as a decorator)."""
    _ACTION_TYPES[cls.kind] = cls
    return cls


def action_from_dict(d: dict[str, Any]) -> Action:
    cls = _ACTION_TYPES[d["kind"]]
    kwargs = {k: v for k, v in d.items() if k not in ("kind", "player")}
    if "die_ids" in kwargs:
        kwargs["die_ids"] = tuple(kwargs["die_ids"])
    return cls(Player(d["player"]), **kwargs)
