"""Replays: a game is fully defined by ``(scenario, seed, actions)``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skyteam.core.actions import Action, action_from_dict
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

FORMAT_VERSION = 1


@dataclass(slots=True)
class GameReplay:
    scenario_id: str
    seed: int
    actions: list[Action] = field(default_factory=list)
    result: dict[str, Any] | None = None

    @classmethod
    def from_game(cls, game: SkyTeamGame) -> "GameReplay":
        status, reason = game.get_result()
        return cls(game.scenario.id, game.state.seed, list(game.actions),
                   {"status": status.value, "terminal_reason": reason})

    def to_dict(self) -> dict[str, Any]:
        return {"format": FORMAT_VERSION, "scenario": self.scenario_id, "seed": self.seed,
                "actions": [a.to_dict() for a in self.actions], "result": self.result}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameReplay":
        if d.get("format") != FORMAT_VERSION:
            raise ValueError(f"unsupported replay format {d.get('format')}")
        return cls(d["scenario"], d["seed"], [action_from_dict(a) for a in d["actions"]], d.get("result"))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "GameReplay":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def run(self, strict: bool = True) -> SkyTeamGame:
        """Re-play every action from scratch. Raises if the recorded result is not reproduced."""
        game = SkyTeamGame(load_scenario(self.scenario_id), config=GameConfig(strict=strict))
        game.reset(self.seed)
        for action in self.actions:
            game.step(action)
        if self.result is not None:
            status, reason = game.get_result()
            if (status.value, reason) != (self.result["status"], self.result["terminal_reason"]):
                raise AssertionError(f"replay diverged: got {status.value}/{reason}, recorded {self.result}")
        return game


DEFAULT_GAMES_DIR = Path("games")


def save_finished_game(game: SkyTeamGame, directory: str | Path = DEFAULT_GAMES_DIR) -> Path:
    """Store a finished game as a replay file (the raw data the imitation trainer learns from)."""
    import time

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    status, _ = game.get_result()
    name = f"{time.strftime('%Y%m%d-%H%M%S')}_{game.scenario.id}_{game.state.seed}_{status.value}.json"
    path = directory / name
    GameReplay.from_game(game).save(path)
    return path
