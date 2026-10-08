"""Immutable scenario definitions (airports, tracks, scenarios).

These objects are configuration: they never change during a game and are not part of
``GameState``. The state only stores the scenario id and indexes into these tracks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from skyteam.core.enums import Player


@dataclass(frozen=True, slots=True)
class ApproachSpace:
    traffic: int = 0                                  # Airplane tokens at setup (R-SET-07)
    airport: bool = False
    traffic_dice: int = 0                             # Traffic die icons (R-TRD-01)
    allowed_axis: frozenset[int] | None = None        # Turns (R-TRN-01); None = no constraint


@dataclass(frozen=True, slots=True)
class ApproachTrack:
    id: str
    airport_code: str
    spaces: tuple[ApproachSpace, ...]
    verified: bool = False

    @property
    def airport_index(self) -> int:
        return len(self.spaces) - 1


@dataclass(frozen=True, slots=True)
class AltitudeSpace:
    altitude: int
    first_player: Player
    reroll: bool = False
    final: bool = False


@dataclass(frozen=True, slots=True)
class AltitudeTrack:
    id: str
    spaces: tuple[AltitudeSpace, ...]
    verified: bool = False

    @property
    def final_index(self) -> int:
        return len(self.spaces) - 1


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    id: str
    params: dict = field(default_factory=dict, hash=False, compare=False)


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    airport_code: str
    airport_name: str
    difficulty: str
    approach_track: ApproachTrack
    altitude_track: AltitudeTrack
    modules: tuple[ModuleSpec, ...] = ()
    special_abilities: int = 0
    panel: str = "base"
    description: str = ""
    verified: bool = False
