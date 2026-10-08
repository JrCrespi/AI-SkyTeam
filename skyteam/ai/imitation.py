"""Learning from recorded games: ``python -m skyteam.ai.imitation --data games --out runs/bc.pt``.

Every game played in the HUD or the terminal is saved as a replay (``games/``). This module
replays them, rebuilds what the acting player could see at each decision, and trains the same
network used by self-play to choose the move that was played (behaviour cloning). Moves from
won games can be weighted more. The result can then keep improving by self-play:
``python -m skyteam.ai.ppo --init runs/bc.pt``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from skyteam.core.enums import GameStatus
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.replay import GameReplay
from skyteam.scenarios.loader import load_scenario

from .action_mask import action_mask
from .action_space import ActionSpace
from .observation import vector_observation
from .ppo import PolicyNet, load_model, save_model


@dataclass
class Dataset:
    obs: np.ndarray        # (N, obs_size) float32
    mask: np.ndarray       # (N, action_size) bool
    action: np.ndarray     # (N,) int64
    outcome: np.ndarray    # (N,) float32, +1 won / -1 lost, from the game the move belongs to
    games: int
    won_games: int

    def __len__(self) -> int:
        return len(self.action)


def build_dataset(replays: list[GameReplay]) -> Dataset:
    obs, masks, actions, outcomes = [], [], [], []
    won = 0
    for replay in replays:
        game = SkyTeamGame(load_scenario(replay.scenario_id), config=GameConfig(keep_undo=False))
        game.reset(replay.seed)
        space = ActionSpace(game.panel)
        rows = []
        for action in replay.actions:
            player = action.player
            rows.append((vector_observation(game, player), action_mask(game, space, player),
                         space.encode(action, game.state)))
            game.step(action)
        status, _ = game.get_result()
        result = 1.0 if status is GameStatus.WON else -1.0
        won += status is GameStatus.WON
        for o, m, a in rows:
            obs.append(o)
            masks.append(m)
            actions.append(a)
            outcomes.append(result)
    return Dataset(np.array(obs, np.float32), np.array(masks, bool), np.array(actions, np.int64),
                   np.array(outcomes, np.float32), len(replays), won)


def load_replays(directory: str | Path) -> list[GameReplay]:
    return [GameReplay.load(p) for p in sorted(Path(directory).glob("*.json"))]


def train_imitation(data: Dataset, init: str | None = None, epochs: int = 30, lr: float = 1e-3,
                    win_weight: float = 2.0, hidden: int = 256, seed: int = 0) -> PolicyNet:
    """Cross-entropy on the played move (masked logits) plus the value head fitted to the outcome."""
    torch.manual_seed(seed)
    if init:
        net, _ = load_model(init)
    else:
        net = PolicyNet(data.obs.shape[1], data.mask.shape[1], hidden)
    net.train()
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs, mask = torch.from_numpy(data.obs), torch.from_numpy(data.mask)
    act, outcome = torch.from_numpy(data.action), torch.from_numpy(data.outcome)
    weight = torch.where(outcome > 0, torch.tensor(win_weight), torch.tensor(1.0))
    n = len(data)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for s in range(0, n, 512):
            idx = perm[s:s + 512]
            logits, value = net(obs[idx], mask[idx])
            ce = nn.functional.cross_entropy(logits, act[idx], reduction="none")
            loss = (ce * weight[idx]).mean() + 0.5 * (value - outcome[idx]).pow(2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval()
    return net


def accuracy(net: PolicyNet, data: Dataset) -> float:
    with torch.no_grad():
        logits, _ = net(torch.from_numpy(data.obs), torch.from_numpy(data.mask))
    return float((logits.argmax(-1).numpy() == data.action).mean()) if len(data) else 0.0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train the Sky Team network from recorded games.")
    parser.add_argument("--data", default="games", help="folder with replay files")
    parser.add_argument("--out", default="runs/bc.pt")
    parser.add_argument("--init", default=None, help="start from an existing model (.pt)")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--win-weight", type=float, default=2.0, help="weight of moves from won games")
    args = parser.parse_args(argv)
    replays = load_replays(args.data)
    if not replays:
        raise SystemExit(f"no replay files in {args.data}")
    data = build_dataset(replays)
    net = train_imitation(data, args.init, args.epochs, win_weight=args.win_weight)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    report = {"games": data.games, "won_games": data.won_games, "moves": len(data),
              "accuracy": round(accuracy(net, data), 3)}
    save_model(net, args.out, {"imitation": report, "data": str(args.data)})
    print(json.dumps(report))


if __name__ == "__main__":
    main()
