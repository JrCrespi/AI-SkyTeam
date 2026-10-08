"""``GameState``: the complete, serialisable state of one game.

Pure data. No rules live here; mechanics are functions that read and mutate a state.
Every field is a primitive, an enum, or a list/dict of those, so ``to_dict``/``from_dict``
round-trip exactly and ``copy`` is cheap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import DecisionKind, GamePhase, GameStatus, Player

DISCARDED = "_discarded"   # DieState.slot of a die discarded without effect (P2)


@dataclass(slots=True)
class DieState:
    die_id: int                 # global id; pilot dice first, then copilot
    owner: Player
    value: int | None = None    # None before the roll
    slot: str | None = None     # slot id once placed

    @property
    def placed(self) -> bool:
        return self.slot is not None

    def copy(self) -> "DieState":
        return DieState(self.die_id, self.owner, self.value, self.slot)

    def to_dict(self) -> dict[str, Any]:
        return {"die_id": self.die_id, "owner": self.owner.value, "value": self.value, "slot": self.slot}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DieState":
        return cls(d["die_id"], Player(d["owner"]), d["value"], d["slot"])


@dataclass(slots=True)
class PendingDecision:
    kind: DecisionKind
    player: Player
    data: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "PendingDecision":
        return PendingDecision(self.kind, self.player, dict(self.data))

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "player": self.player.value, "data": dict(self.data)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PendingDecision":
        return cls(DecisionKind(d["kind"]), Player(d["player"]), dict(d["data"]))


@dataclass(slots=True)
class GameState:
    scenario_id: str
    seed: int

    # flow
    round: int = 0
    phase: GamePhase = GamePhase.ROUND_START
    active_player: Player | None = None
    strategy_confirmed: list[Player] = field(default_factory=list)
    pending: list[PendingDecision] = field(default_factory=list)
    reroll_window_done: bool = False            # P3: the window was offered for the current turn

    # dice and panel
    dice: list[DieState] = field(default_factory=list)
    slots: dict[str, str | None] = field(default_factory=dict)  # slot id -> piece key ("die:3") or None
    switches: dict[str, bool] = field(default_factory=dict)     # slot id -> activated

    # gauges
    axis: int = 0               # <0 tilted toward the Pilot, >0 toward the Co-Pilot
    aero_blue: int = 0          # marker between aero_blue and aero_blue+1
    aero_orange: int = 0
    brakes_deployed: int = 0    # index into PanelConstants.brake_thresholds
    coffee: int = 0
    reroll_supply: int = 0

    # tracks
    altitude_index: int = 0
    altitude_rerolls: list[bool] = field(default_factory=list)  # reroll token still on altitude space i
    approach_position: int = 0
    traffic: list[int] = field(default_factory=list)            # Airplane tokens per approach space
    plane_supply: int = 0

    # values recorded during the round
    last_speed: int | None = None
    landing_speed_ok: bool | None = None        # R-BRK-07: set when the final-round engines resolve

    # extensions
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    abilities: dict[str, dict[str, Any]] = field(default_factory=dict)

    # random streams (state of each stream)
    rng: dict[str, int] = field(default_factory=dict)

    # outcome
    status: GameStatus = GameStatus.IN_PROGRESS
    terminal_reason: str | None = None

    # ------------------------------------------------------------------ helpers
    def die(self, die_id: int) -> DieState:
        return self.dice[die_id]

    def dice_of(self, player: Player) -> list[DieState]:
        return [d for d in self.dice if d.owner is player]

    def hidden_dice(self, player: Player) -> list[DieState]:
        return [d for d in self.dice if d.owner is player and not d.placed]

    def die_in(self, slot_id: str) -> DieState | None:
        key = self.slots.get(slot_id)
        if key is None or not key.startswith("die:"):
            return None
        return self.dice[int(key[4:])]

    @property
    def is_terminal(self) -> bool:
        return self.status is not GameStatus.IN_PROGRESS

    # ------------------------------------------------------------------ copy / serialisation
    def copy(self) -> "GameState":
        return GameState(
            scenario_id=self.scenario_id,
            seed=self.seed,
            round=self.round,
            phase=self.phase,
            active_player=self.active_player,
            strategy_confirmed=list(self.strategy_confirmed),
            pending=[p.copy() for p in self.pending],
            reroll_window_done=self.reroll_window_done,
            dice=[d.copy() for d in self.dice],
            slots=dict(self.slots),
            switches=dict(self.switches),
            axis=self.axis,
            aero_blue=self.aero_blue,
            aero_orange=self.aero_orange,
            brakes_deployed=self.brakes_deployed,
            coffee=self.coffee,
            reroll_supply=self.reroll_supply,
            altitude_index=self.altitude_index,
            altitude_rerolls=list(self.altitude_rerolls),
            approach_position=self.approach_position,
            traffic=list(self.traffic),
            plane_supply=self.plane_supply,
            last_speed=self.last_speed,
            landing_speed_ok=self.landing_speed_ok,
            modules=_deep_copy_json(self.modules),
            abilities=_deep_copy_json(self.abilities),
            rng=dict(self.rng),
            status=self.status,
            terminal_reason=self.terminal_reason,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "round": self.round,
            "phase": self.phase.value,
            "active_player": self.active_player.value if self.active_player else None,
            "strategy_confirmed": [p.value for p in self.strategy_confirmed],
            "pending": [p.to_dict() for p in self.pending],
            "reroll_window_done": self.reroll_window_done,
            "dice": [d.to_dict() for d in self.dice],
            "slots": dict(self.slots),
            "switches": dict(self.switches),
            "axis": self.axis,
            "aero_blue": self.aero_blue,
            "aero_orange": self.aero_orange,
            "brakes_deployed": self.brakes_deployed,
            "coffee": self.coffee,
            "reroll_supply": self.reroll_supply,
            "altitude_index": self.altitude_index,
            "altitude_rerolls": list(self.altitude_rerolls),
            "approach_position": self.approach_position,
            "traffic": list(self.traffic),
            "plane_supply": self.plane_supply,
            "last_speed": self.last_speed,
            "landing_speed_ok": self.landing_speed_ok,
            "modules": _deep_copy_json(self.modules),
            "abilities": _deep_copy_json(self.abilities),
            "rng": {k: str(v) for k, v in self.rng.items()},  # 64-bit ints as strings (JSON-safe)
            "status": self.status.value,
            "terminal_reason": self.terminal_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameState":
        return cls(
            scenario_id=d["scenario_id"],
            seed=d["seed"],
            round=d["round"],
            phase=GamePhase(d["phase"]),
            active_player=Player(d["active_player"]) if d["active_player"] else None,
            strategy_confirmed=[Player(p) for p in d["strategy_confirmed"]],
            pending=[PendingDecision.from_dict(p) for p in d["pending"]],
            reroll_window_done=d["reroll_window_done"],
            dice=[DieState.from_dict(x) for x in d["dice"]],
            slots=dict(d["slots"]),
            switches=dict(d["switches"]),
            axis=d["axis"],
            aero_blue=d["aero_blue"],
            aero_orange=d["aero_orange"],
            brakes_deployed=d["brakes_deployed"],
            coffee=d["coffee"],
            reroll_supply=d["reroll_supply"],
            altitude_index=d["altitude_index"],
            altitude_rerolls=list(d["altitude_rerolls"]),
            approach_position=d["approach_position"],
            traffic=list(d["traffic"]),
            plane_supply=d["plane_supply"],
            last_speed=d["last_speed"],
            landing_speed_ok=d["landing_speed_ok"],
            modules=_deep_copy_json(d["modules"]),
            abilities=_deep_copy_json(d["abilities"]),
            rng={k: int(v) for k, v in d["rng"].items()},
            status=GameStatus(d["status"]),
            terminal_reason=d["terminal_reason"],
        )


def _deep_copy_json(value: Any) -> Any:
    """Copy nested dict/list structures of primitives (module state is JSON-like)."""
    if isinstance(value, dict):
        return {k: _deep_copy_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy_json(v) for v in value]
    return value
