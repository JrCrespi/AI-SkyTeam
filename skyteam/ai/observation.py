"""Observations for learning agents.

``structured_observation`` is the engine's per-player dict. ``vector_observation`` turns it
into a flat list of floats in [0, 1] with a fixed layout, described by ``vector_layout``
(and documented in docs/ai_environment.md). Only information the player may know is used:
the vector is built from the structured observation, never from the full state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from skyteam.core.enums import DecisionKind, GamePhase, GameStatus, Player
from skyteam.core.game import SkyTeamGame

MAX_ALTITUDE_SPACES = 7
MAX_APPROACH_SPACES = 12
MAX_TRAFFIC_PER_SPACE = 4
MAX_SPEED = 18
PHASES = tuple(GamePhase)
STATUSES = tuple(GameStatus)
DECISIONS = tuple(DecisionKind)


@dataclass(frozen=True, slots=True)
class Segment:
    name: str
    size: int
    description: str


def vector_layout(game: SkyTeamGame) -> list[Segment]:
    c = game.panel.constants
    n_slots = len(game.panel.slots)
    n_switches = len(game.panel.switch_slots())
    axis_range = 2 * c.axis_spin_at + 1
    return [
        Segment("round", 1, "round / number of altitude spaces"),
        Segment("phase", len(PHASES), "one-hot GamePhase"),
        Segment("me_is_pilot", 1, "1 if the observing player is the Pilot"),
        Segment("me_is_current", 1, "1 if the observing player must act now"),
        Segment("me_is_active", 1, "1 if it is the observing player's placement turn"),
        Segment("pending", len(DECISIONS), "one-hot kind of the first pending decision (zeros if none)"),
        Segment("own_dice", c.dice_per_player * (c.die_sides + 1),
                "per own die ordinal: one-hot value (6) + 'still hidden' flag; zeros once placed"),
        Segment("partner_hidden", 1, "partner hidden dice count / dice per player"),
        Segment("slots_occupied", n_slots, "per panel slot (panel order): 1 if occupied"),
        Segment("slots_value", n_slots, "per panel slot: value of the piece / die sides (0 if empty)"),
        Segment("slots_by_pilot", n_slots, "per panel slot: 1 if the piece belongs to the Pilot"),
        Segment("switches", n_switches, "per switch slot (panel order): 1 if activated"),
        Segment("axis", axis_range, f"one-hot axis position {-c.axis_spin_at}..{c.axis_spin_at} (clamped)"),
        Segment("aero_blue", 1, "blue marker / 12"),
        Segment("aero_orange", 1, "orange marker / 12"),
        Segment("brakes", len(c.brake_thresholds), "one-hot number of brakes deployed"),
        Segment("coffee", c.coffee_max + 1, "one-hot coffee tokens"),
        Segment("reroll_supply", 1, "reroll tokens in supply / reroll tokens in the game"),
        Segment("altitude", MAX_ALTITUDE_SPACES, "one-hot altitude index"),
        Segment("altitude_rerolls", MAX_ALTITUDE_SPACES, "per altitude space: reroll token still there"),
        Segment("first_player_pilot", MAX_ALTITUDE_SPACES, "per altitude space: 1 if the Pilot starts that round"),
        Segment("approach", MAX_APPROACH_SPACES, "one-hot approach position"),
        Segment("distance_to_airport", 1, "remaining spaces / max approach spaces"),
        Segment("traffic_ahead", MAX_APPROACH_SPACES,
                f"airplanes on position+k (k=0..), / {MAX_TRAFFIC_PER_SPACE}, zeros past the airport"),
        Segment("traffic_total", 1, "airplanes on the track / plane tokens"),
        Segment("last_speed", 1, f"last speed this round / {MAX_SPEED} (0 if not resolved)"),
        Segment("final_round", 1, "1 during the landing round"),
        Segment("status", len(STATUSES), "one-hot GameStatus"),
    ]


def vector_size(game: SkyTeamGame) -> int:
    return sum(seg.size for seg in vector_layout(game))


def _one_hot(index: int, size: int) -> list[float]:
    v = [0.0] * size
    if 0 <= index < size:
        v[index] = 1.0
    return v


def vector_observation(game: SkyTeamGame, player: Player, obs: dict[str, Any] | None = None) -> list[float]:
    obs = obs if obs is not None else game.get_observation(player)
    c = game.panel.constants
    panel_slots = game.panel.slots
    alt_track = game.scenario.altitude_track
    approach = game.scenario.approach_track
    out: list[float] = []
    add = out.extend

    add([obs["round"] / len(alt_track.spaces)])
    add(_one_hot(PHASES.index(GamePhase(obs["phase"])), len(PHASES)))
    add([1.0 if player is Player.PILOT else 0.0])
    add([1.0 if game.current_player is player else 0.0])
    add([1.0 if obs["active_player"] == player.value else 0.0])
    pending = obs["pending"][0]["kind"] if obs["pending"] else None
    add(_one_hot(DECISIONS.index(DecisionKind(pending)), len(DECISIONS)) if pending else [0.0] * len(DECISIONS))

    offset = 0 if player is Player.PILOT else c.dice_per_player
    hidden = {d["die_id"]: d["value"] for d in obs["own_hidden_dice"]}
    for ordinal in range(c.dice_per_player):
        value = hidden.get(offset + ordinal)
        if value is None:
            add([0.0] * (c.die_sides + 1))
        else:
            add(_one_hot(value - 1, c.die_sides) + [1.0])
    add([obs["partner_hidden_dice_count"] / c.dice_per_player])

    placed = {f"die:{d['die_id']}": d for d in obs["placed_dice"]}
    pieces = [placed.get(obs["slots"].get(s.id) or "") for s in panel_slots]
    add([1.0 if p else 0.0 for p in pieces])
    add([p["value"] / c.die_sides if p else 0.0 for p in pieces])
    add([1.0 if p and p["owner"] == Player.PILOT.value else 0.0 for p in pieces])
    add([1.0 if obs["switches"].get(s.id) else 0.0 for s in game.panel.switch_slots()])

    axis = max(-c.axis_spin_at, min(c.axis_spin_at, obs["axis"]))
    add(_one_hot(axis + c.axis_spin_at, 2 * c.axis_spin_at + 1))
    add([obs["aero_blue"] / 12, obs["aero_orange"] / 12])
    add(_one_hot(obs["brakes_deployed"], len(c.brake_thresholds)))
    add(_one_hot(obs["coffee"], c.coffee_max + 1))
    add([obs["reroll_supply"] / c.reroll_tokens])

    add(_one_hot(obs["altitude_index"], MAX_ALTITUDE_SPACES))
    add(_pad([1.0 if r else 0.0 for r in obs["altitude_rerolls"]], MAX_ALTITUDE_SPACES))
    add(_pad([1.0 if s.first_player is Player.PILOT else 0.0 for s in alt_track.spaces], MAX_ALTITUDE_SPACES))

    pos = obs["approach_position"]
    add(_one_hot(pos, MAX_APPROACH_SPACES))
    add([(approach.airport_index - pos) / MAX_APPROACH_SPACES])
    traffic = obs["traffic"]
    add(_pad([min(t, MAX_TRAFFIC_PER_SPACE) / MAX_TRAFFIC_PER_SPACE for t in traffic[pos:]], MAX_APPROACH_SPACES))
    add([sum(traffic) / c.plane_tokens])
    add([(obs["last_speed"] or 0) / MAX_SPEED])
    add([1.0 if alt_track.spaces[obs["altitude_index"]].final else 0.0])
    add(_one_hot(STATUSES.index(GameStatus(obs["status"])), len(STATUSES)))
    return out


def _pad(values: list[float], size: int) -> list[float]:
    if len(values) > size:
        raise ValueError(f"track longer than the observation supports ({len(values)} > {size})")
    return values + [0.0] * (size - len(values))
