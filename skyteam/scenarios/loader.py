"""Load and validate scenario data from JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skyteam.core.data_files import DATA_DIR, read_json
from skyteam.core.enums import Player
from skyteam.core.exceptions import DataError

from .model import (
    AltitudeSpace,
    AltitudeTrack,
    ApproachSpace,
    ApproachTrack,
    ModuleSpec,
    Scenario,
)


def parse_approach_track(raw: dict[str, Any]) -> ApproachTrack:
    try:
        spaces = tuple(
            ApproachSpace(
                traffic=int(s.get("traffic", 0)),
                airport=bool(s.get("airport", False)),
                traffic_dice=int(s.get("traffic_dice", 0)),
                allowed_axis=frozenset(s["allowed_axis"]) if s.get("allowed_axis") is not None else None,
            )
            for s in raw["spaces"]
        )
        track = ApproachTrack(
            id=raw["id"], airport_code=raw["airport"], spaces=spaces, verified=bool(raw.get("verified", False))
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(f"malformed approach track: {exc}") from exc
    _validate_approach(track)
    return track


def _validate_approach(track: ApproachTrack) -> None:
    if len(track.spaces) < 2:
        raise DataError(f"approach track {track.id}: needs at least 2 spaces")
    airports = [i for i, s in enumerate(track.spaces) if s.airport]
    if airports != [track.airport_index]:
        raise DataError(f"approach track {track.id}: exactly the last space must be the airport")
    if any(s.traffic < 0 or s.traffic_dice < 0 for s in track.spaces):
        raise DataError(f"approach track {track.id}: negative counts")


def parse_altitude_track(raw: dict[str, Any]) -> AltitudeTrack:
    try:
        spaces = tuple(
            AltitudeSpace(
                altitude=int(s["altitude"]),
                first_player=Player(s["first_player"]),
                reroll=bool(s.get("reroll", False)),
                final=bool(s.get("final", False)),
            )
            for s in raw["spaces"]
        )
        track = AltitudeTrack(id=raw["id"], spaces=spaces, verified=bool(raw.get("verified", False)))
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(f"malformed altitude track: {exc}") from exc
    finals = [i for i, s in enumerate(track.spaces) if s.final]
    if finals != [track.final_index]:
        raise DataError(f"altitude track {track.id}: exactly the last space must be final")
    return track


def _find(kind: str, item_id: str, extra_dirs: tuple[Path, ...]) -> Path:
    for base in (*extra_dirs, DATA_DIR):
        path = base / kind / f"{item_id}.json"
        if path.exists():
            return path
    raise DataError(f"{kind}: '{item_id}' not found")


def load_approach_track(track_id: str, extra_dirs: tuple[Path, ...] = ()) -> ApproachTrack:
    return parse_approach_track(read_json(_find("approach_tracks", track_id, extra_dirs)))


def load_altitude_track(track_id: str, extra_dirs: tuple[Path, ...] = ()) -> AltitudeTrack:
    return parse_altitude_track(read_json(_find("altitude_tracks", track_id, extra_dirs)))


def parse_scenario(raw: dict[str, Any], extra_dirs: tuple[Path, ...] = ()) -> Scenario:
    try:
        approach = load_approach_track(raw["approach_track"], extra_dirs)
        altitude = load_altitude_track(raw["altitude_track"], extra_dirs)
        scenario = Scenario(
            id=raw["id"],
            airport_code=raw["airport"],
            airport_name=raw.get("airport_name", raw["airport"]),
            difficulty=raw["difficulty"],
            approach_track=approach,
            altitude_track=altitude,
            modules=tuple(ModuleSpec(m["id"], dict(m.get("params", {}))) for m in raw.get("modules", [])),
            special_abilities=int(raw.get("special_abilities", 0)),
            panel=raw.get("panel", "base"),
            description=raw.get("description", ""),
            verified=bool(raw.get("verified", False)) and approach.verified and altitude.verified,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(f"malformed scenario: {exc}") from exc
    if approach.airport_code != scenario.airport_code:
        raise DataError(f"scenario {scenario.id}: approach track belongs to {approach.airport_code}")
    return scenario


def load_scenario(scenario_id: str, extra_dirs: tuple[Path, ...] = ()) -> Scenario:
    return parse_scenario(read_json(_find("scenarios", scenario_id, extra_dirs)), extra_dirs)
