"""``SkyTeamEnv``: a library-agnostic, turn-based multi-agent environment.

The engine decides who acts (``current_player``); the environment never knows whether a
player is a human or an agent. Adapters for Gymnasium / PettingZoo can wrap this class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from skyteam.core.enums import Player
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario
from skyteam.scenarios.model import Scenario

from .action_mask import action_mask
from .action_space import ActionSpace
from .observation import vector_observation, vector_size
from .rewards import RewardFn, SparseReward


@dataclass(slots=True)
class Observation:
    player: Player
    structured: dict[str, Any]
    vector: list[float]
    mask: list[bool]


class SkyTeamEnv:
    def __init__(self, scenario: str | Scenario = "YUL_green", seed: int = 0,
                 reward: RewardFn | None = None, max_steps: int = 2000) -> None:
        self.scenario = load_scenario(scenario) if isinstance(scenario, str) else scenario
        self.seed = seed
        self.reward = reward or SparseReward()
        self.max_steps = max_steps
        self.game = SkyTeamGame(self.scenario, config=GameConfig(keep_undo=False))
        self.space = ActionSpace(self.game.panel)
        self.steps = 0
        self.truncated = False

    # ------------------------------------------------------------------ info
    @property
    def action_size(self) -> int:
        return self.space.size

    @property
    def observation_size(self) -> int:
        return vector_size(self.game)

    @property
    def current_player(self) -> Player | None:
        return self.game.current_player

    @property
    def done(self) -> bool:
        return self.game.is_terminal() or self.truncated

    # ------------------------------------------------------------------ API
    def reset(self, seed: int | None = None) -> Observation:
        if seed is not None:
            self.seed = seed
        self.game.reset(self.seed)
        self.steps = 0
        self.truncated = False
        return self.observe(self.current_player)

    def observe(self, player: Player) -> Observation:
        structured = self.game.get_observation(player)
        return Observation(player, structured, vector_observation(self.game, player, structured),
                           action_mask(self.game, self.space, player))

    def legal_actions(self) -> list[int]:
        player = self.current_player
        if player is None:
            return []
        return sorted({self.space.encode(a, self.game.state) for a in self.game.get_legal_actions(player)})

    def step(self, action_index: int) -> tuple[Observation | None, float, bool, bool, dict[str, Any]]:
        """Apply the current player's action. Returns the next player's observation."""
        if self.done:
            raise RuntimeError("step() called on a finished episode; call reset()")
        player = self.current_player
        action = self.space.decode(action_index, player, self.game.state)
        before = self.game.state.copy() if getattr(self.reward, "uses_before", True) else None
        result = self.game.step(action)
        self.steps += 1
        reward = self.reward(before, action, self.game.state)
        terminated = self.game.is_terminal()
        self.truncated = not terminated and self.steps >= self.max_steps
        next_player = self.current_player
        obs = self.observe(next_player) if next_player is not None else None
        info = {"acting_player": player, "next_player": next_player, "status": result.status,
                "terminal_reason": result.terminal_reason, "action": action}
        return obs, reward, terminated, self.truncated, info

    def clone(self) -> "SkyTeamEnv":
        other = SkyTeamEnv.__new__(SkyTeamEnv)
        other.scenario, other.seed, other.reward, other.max_steps = (
            self.scenario, self.seed, self.reward, self.max_steps)
        other.game = self.game.clone()
        other.space = self.space
        other.steps, other.truncated = self.steps, self.truncated
        return other
