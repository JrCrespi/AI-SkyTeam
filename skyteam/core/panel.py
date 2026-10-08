"""Control Panel layout, loaded from data.

Mechanics never hard-code slot ids or value constraints: they read them from the
``PanelLayout``. Modules can extend or replace slots (e.g. Ice Brakes covering the brakes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data_files import DATA_DIR, read_json
from .enums import Player, SlotKind
from .exceptions import DataError

SWITCH_KINDS = frozenset({SlotKind.LANDING_GEAR, SlotKind.FLAPS, SlotKind.BRAKES})


@dataclass(frozen=True, slots=True)
class SlotDef:
    id: str
    kind: SlotKind
    owners: frozenset[Player]
    values: frozenset[int] | None = None   # None = any value
    requires: str | None = None            # switch that must already be activated (order)
    mandatory: bool = False

    @property
    def has_switch(self) -> bool:
        return self.kind in SWITCH_KINDS

    def accepts_value(self, value: int) -> bool:
        return self.values is None or value in self.values


@dataclass(frozen=True, slots=True)
class PanelConstants:
    dice_per_player: int
    die_sides: int
    axis_spin_at: int
    aero_blue_start: int
    aero_orange_start: int
    brake_thresholds: tuple[int, ...]
    coffee_max: int
    coffee_max_per_die: int
    plane_tokens: int
    reroll_tokens: int


@dataclass(frozen=True, slots=True)
class PanelLayout:
    id: str
    constants: PanelConstants
    slots: tuple[SlotDef, ...]
    _by_id: dict[str, SlotDef] = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self) -> None:
        by_id = {slot.id: slot for slot in self.slots}
        if len(by_id) != len(self.slots):
            raise DataError(f"panel {self.id}: duplicate slot ids")
        for slot in self.slots:
            if slot.requires is not None and slot.requires not in by_id:
                raise DataError(f"panel {self.id}: {slot.id} requires unknown slot {slot.requires}")
        self._by_id.update(by_id)

    def slot(self, slot_id: str) -> SlotDef:
        return self._by_id[slot_id]

    def has_slot(self, slot_id: str) -> bool:
        return slot_id in self._by_id

    def slots_of(self, kind: SlotKind) -> tuple[SlotDef, ...]:
        return tuple(s for s in self.slots if s.kind is kind)

    def switch_slots(self) -> tuple[SlotDef, ...]:
        return tuple(s for s in self.slots if s.has_switch)

    def mandatory_slots(self) -> tuple[SlotDef, ...]:
        return tuple(s for s in self.slots if s.mandatory)

    def with_slots(self, slots: tuple[SlotDef, ...]) -> "PanelLayout":
        """Return a copy with a different slot list (used by modules)."""
        return PanelLayout(id=self.id, constants=self.constants, slots=slots)


def _parse_slot(raw: dict[str, Any]) -> SlotDef:
    values = raw.get("values")
    return SlotDef(
        id=raw["id"],
        kind=SlotKind(raw["kind"]),
        owners=frozenset(Player(p) for p in raw["owners"]),
        values=frozenset(values) if values is not None else None,
        requires=raw.get("requires"),
        mandatory=bool(raw.get("mandatory", False)),
    )


def parse_panel(raw: dict[str, Any]) -> PanelLayout:
    try:
        c = raw["constants"]
        constants = PanelConstants(
            dice_per_player=c["dice_per_player"],
            die_sides=c["die_sides"],
            axis_spin_at=c["axis_spin_at"],
            aero_blue_start=c["aero_blue_start"],
            aero_orange_start=c["aero_orange_start"],
            brake_thresholds=tuple(c["brake_thresholds"]),
            coffee_max=c["coffee_max"],
            coffee_max_per_die=c["coffee_max_per_die"],
            plane_tokens=c["plane_tokens"],
            reroll_tokens=c["reroll_tokens"],
        )
        slots = tuple(_parse_slot(s) for s in raw["slots"])
    except (KeyError, ValueError, TypeError) as exc:
        raise DataError(f"malformed panel data: {exc}") from exc
    return PanelLayout(id=raw["id"], constants=constants, slots=slots)


def load_panel(panel_id: str = "base") -> PanelLayout:
    return parse_panel(read_json(DATA_DIR / "panel" / f"{panel_id}.json"))
