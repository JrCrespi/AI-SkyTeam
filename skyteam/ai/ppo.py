"""Self-play training with PPO: ``python -m skyteam.ai.ppo --steps 2000000``.

One network plays both seats (parameter sharing). Each decision is taken from the acting
player's own observation (hidden partner dice never reach the network), with the legal-action
mask applied to the logits. Sky Team is cooperative, so both seats share the reward and the
whole game is one trajectory for the advantage estimate.

The network improves only from the games it plays: every update uses the latest batch of
self-play games, and a fixed set of evaluation seeds measures the win rate over time.
Requires ``torch`` and ``numpy`` (``pip install -e .[train]``); the engine does not.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from skyteam.core.actions import Action
from skyteam.core.enums import GameStatus, Player
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

from .action_mask import action_mask
from .action_space import ActionSpace
from .environment import SkyTeamEnv
from .observation import vector_observation
from .rewards import training_reward


# ---------------------------------------------------------------- network
class PolicyNet(nn.Module):
    def __init__(self, obs_size: int, action_size: int, hidden: int = 256) -> None:
        super().__init__()
        self.obs_size, self.action_size, self.hidden = obs_size, action_size, hidden
        self.body = nn.Sequential(
            nn.Linear(obs_size, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.pi = nn.Linear(hidden, action_size)
        self.v = nn.Linear(hidden, 1)
        nn.init.orthogonal_(self.pi.weight, 0.01)
        nn.init.zeros_(self.pi.bias)

    def forward(self, obs: torch.Tensor, mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.body(obs)
        logits = self.pi(h).masked_fill(~mask, -1e9)
        return logits, self.v(h).squeeze(-1)


def save_model(net: PolicyNet, path: str | Path, meta: dict) -> None:
    torch.save({"state_dict": net.state_dict(), "obs_size": net.obs_size, "action_size": net.action_size,
                "hidden": net.hidden, "meta": meta}, path)


def load_model(path: str | Path) -> tuple[PolicyNet, dict]:
    data = torch.load(path, map_location="cpu", weights_only=False)
    net = PolicyNet(data["obs_size"], data["action_size"], data["hidden"])
    net.load_state_dict(data["state_dict"])
    net.eval()
    return net, data.get("meta", {})


# ---------------------------------------------------------------- agent
class ModelAgent:
    """Plays with a trained network. Usable as a ``simulate`` policy: ``agent(game, legal, rng)``."""

    def __init__(self, path: str | Path, greedy: bool = True) -> None:
        self.net, self.meta = load_model(path)
        self.greedy = greedy
        self._space: ActionSpace | None = None

    def act(self, game: SkyTeamGame, player: Player, rng: random.Random | None = None) -> Action:
        if self._space is None or self._space.panel is not game.panel:
            self._space = ActionSpace(game.panel)
        obs = torch.tensor([vector_observation(game, player)], dtype=torch.float32)
        mask = torch.tensor([action_mask(game, self._space, player)])
        with torch.no_grad():
            logits, _ = self.net(obs, mask)
        if self.greedy:
            index = int(logits.argmax(-1))
        else:
            gen = torch.Generator().manual_seed((rng or random).randrange(2**63))
            index = int(torch.multinomial(torch.softmax(logits, -1), 1, generator=gen))
        return self._space.decode(index, player, game.state)

    def __call__(self, game: SkyTeamGame, legal: list[Action], rng: random.Random) -> Action:
        return self.act(game, game.current_player, rng)


# ---------------------------------------------------------------- evaluation
def evaluate(net: PolicyNet, scenario: str, games: int, seed: int) -> dict:
    """Greedy play on fixed seeds. Returns win rate and outcome counts."""
    sc = load_scenario(scenario)
    net.eval()
    outcomes: Counter[str] = Counter()
    rounds = 0
    space = None
    for i in range(games):
        game = SkyTeamGame(sc, config=GameConfig(keep_undo=False))
        game.reset(seed + i)
        space = space or ActionSpace(game.panel)
        while not game.is_terminal():
            p = game.current_player
            obs = torch.tensor([vector_observation(game, p)], dtype=torch.float32)
            mask = torch.tensor([action_mask(game, space, p)])
            with torch.no_grad():
                logits, _ = net(obs, mask)
            game.step(space.decode(int(logits.argmax(-1)), p, game.state))
        status, reason = game.get_result()
        outcomes["won" if status is GameStatus.WON else str(reason)] += 1
        rounds += game.state.round
    return {"win_rate": outcomes["won"] / games, "avg_round": rounds / games,
            "outcomes": dict(outcomes.most_common())}


# ---------------------------------------------------------------- parallel environments
def _worker(conn, scenario: str, reward_kwargs: dict, seeds: list[int], seed_stride: int) -> None:
    envs = [SkyTeamEnv(scenario, reward=training_reward(**reward_kwargs)) for _ in seeds]
    next_seeds = list(seeds)
    obs = [env.reset(s) for env, s in zip(envs, next_seeds)]

    def pack():
        return (np.array([o.vector for o in obs], np.float32), np.array([o.mask for o in obs], bool))

    import os

    parent = os.getppid()
    while True:
        try:
            if not conn.poll(5):
                if os.getppid() != parent:     # the trainer was killed: do not linger
                    return
                continue
            cmd, data = conn.recv()
        except (EOFError, OSError):
            return
        if cmd == "obs":
            conn.send(pack())
        elif cmd == "step":
            rewards, dones, results = [], [], []
            for i, (env, a) in enumerate(zip(envs, data)):
                o, r, term, trunc, _ = env.step(int(a))
                rewards.append(r)
                dones.append(float(term or trunc))
                if term or trunc:
                    status, reason = env.game.get_result()
                    results.append("won" if status is GameStatus.WON else str(reason))
                    next_seeds[i] += seed_stride
                    o = env.reset(next_seeds[i])
                obs[i] = o
            conn.send((*pack(), np.array(rewards, np.float32), np.array(dones, np.float32), results))
        else:
            conn.close()
            return


class VecEnv:
    """``envs`` environments split in contiguous blocks over ``workers`` processes."""

    def __init__(self, scenario: str, envs: int, workers: int, reward_kwargs: dict, seed: int) -> None:
        import multiprocessing as mp

        seeds = [seed * 10_000_000 + i for i in range(envs)]
        size = -(-envs // workers)
        self.blocks = [(s, min(s + size, envs)) for s in range(0, envs, size)]
        ctx = mp.get_context("fork")
        self.conns, self.procs = [], []
        for a, b in self.blocks:
            parent, child = ctx.Pipe()
            proc = ctx.Process(target=_worker, args=(child, scenario, reward_kwargs, seeds[a:b], envs), daemon=True)
            proc.start()
            self.conns.append(parent)
            self.procs.append(proc)

    def observe(self):
        for c in self.conns:
            c.send(("obs", None))
        replies = [c.recv() for c in self.conns]
        return np.concatenate([r[0] for r in replies]), np.concatenate([r[1] for r in replies])

    def step(self, actions: np.ndarray):
        for c, (a, b) in zip(self.conns, self.blocks):
            c.send(("step", actions[a:b].tolist()))
        replies = [c.recv() for c in self.conns]
        return (*(np.concatenate([r[k] for r in replies]) for k in range(4)), [x for r in replies for x in r[4]])

    def close(self) -> None:
        for c in self.conns:
            c.send(("close", None))
        for proc in self.procs:
            proc.join(timeout=5)


# ---------------------------------------------------------------- training
@dataclass
class TrainConfig:
    scenario: str = "YUL_green"
    steps: int = 2_000_000
    envs: int = 64
    rollout: int = 128
    epochs: int = 4
    minibatch: int = 2048
    lr: float = 3e-4
    gamma: float = 0.995
    lam: float = 0.95
    clip: float = 0.2
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    round_bonus: float = 0.2
    progress_bonus: float = 1.0
    config_bonus: float = 0.05
    traffic_bonus: float = 0.05
    landing_bonus: float = 0.25
    hidden: int = 256
    workers: int = 4
    seed: int = 0
    eval_every: int = 10
    eval_games: int = 300
    eval_seed: int = 1_000_000
    out: str = "runs/ppo"
    init: str = ""          # start from an existing model (e.g. one trained by imitation)


def train(cfg: TrainConfig, log=print) -> PolicyNet:
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    out = Path(cfg.out)
    out.mkdir(parents=True, exist_ok=True)
    probe = SkyTeamEnv(cfg.scenario)
    reward_kwargs = {"round_bonus": cfg.round_bonus, "progress_bonus": cfg.progress_bonus,
                     "config_bonus": cfg.config_bonus, "traffic_bonus": cfg.traffic_bonus,
                     "landing_bonus": cfg.landing_bonus,
                     "track_length": probe.scenario.approach_track.airport_index}
    vec = VecEnv(cfg.scenario, cfg.envs, max(1, cfg.workers), reward_kwargs, cfg.seed)
    cur_obs, cur_mask = vec.observe()
    if cfg.init:
        net, _ = load_model(cfg.init)
    else:
        net = PolicyNet(probe.observation_size, probe.action_size, cfg.hidden)
    opt = torch.optim.Adam(net.parameters(), lr=cfg.lr, eps=1e-5)
    n, T, A, O = cfg.envs, cfg.rollout, probe.action_size, probe.observation_size

    recent: deque[str] = deque(maxlen=2000)
    history = []
    best = -1.0
    updates = cfg.steps // (n * T)
    start = time.perf_counter()
    for update in range(1, updates + 1):
        frac = 1.0 - (update - 1) / updates
        for g in opt.param_groups:
            g["lr"] = cfg.lr * frac
        b_obs = np.zeros((T, n, O), np.float32)
        b_mask = np.zeros((T, n, A), bool)
        b_act = np.zeros((T, n), np.int64)
        b_logp = np.zeros((T, n), np.float32)
        b_val = np.zeros((T, n), np.float32)
        b_rew = np.zeros((T, n), np.float32)
        b_done = np.zeros((T, n), np.float32)
        net.eval()
        for t in range(T):
            b_obs[t], b_mask[t] = cur_obs, cur_mask
            with torch.no_grad():
                logits, value = net(torch.from_numpy(b_obs[t]), torch.from_numpy(b_mask[t]))
                dist = torch.distributions.Categorical(logits=logits)
                action = dist.sample()
            b_act[t] = action.numpy()
            b_logp[t] = dist.log_prob(action).numpy()
            b_val[t] = value.numpy()
            cur_obs, cur_mask, b_rew[t], b_done[t], results = vec.step(b_act[t])
            recent.extend(results)
        with torch.no_grad():
            _, last_v = net(torch.from_numpy(cur_obs), torch.from_numpy(cur_mask))
        last_v = last_v.numpy()
        adv = np.zeros((T, n), np.float32)
        gae = np.zeros(n, np.float32)
        for t in reversed(range(T)):
            nxt = last_v if t == T - 1 else b_val[t + 1]
            nonterminal = 1.0 - b_done[t]
            delta = b_rew[t] + cfg.gamma * nxt * nonterminal - b_val[t]
            gae = delta + cfg.gamma * cfg.lam * nonterminal * gae
            adv[t] = gae
        ret = adv + b_val

        f_obs = torch.from_numpy(b_obs.reshape(T * n, O))
        f_mask = torch.from_numpy(b_mask.reshape(T * n, A))
        f_act = torch.from_numpy(b_act.reshape(-1))
        f_logp = torch.from_numpy(b_logp.reshape(-1))
        f_adv = torch.from_numpy(adv.reshape(-1))
        f_ret = torch.from_numpy(ret.reshape(-1))
        net.train()
        idx = np.arange(T * n)
        for _ in range(cfg.epochs):
            np.random.shuffle(idx)
            for s in range(0, T * n, cfg.minibatch):
                mb = torch.from_numpy(idx[s:s + cfg.minibatch])
                logits, value = net(f_obs[mb], f_mask[mb])
                dist = torch.distributions.Categorical(logits=logits)
                logp = dist.log_prob(f_act[mb])
                a = f_adv[mb]
                a = (a - a.mean()) / (a.std() + 1e-8)
                ratio = (logp - f_logp[mb]).exp()
                pg = -torch.min(ratio * a, ratio.clamp(1 - cfg.clip, 1 + cfg.clip) * a).mean()
                vf = 0.5 * (value - f_ret[mb]).pow(2).mean()
                ent = dist.entropy().mean()
                loss = pg + cfg.vf_coef * vf - cfg.ent_coef * ent
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()

        steps = update * n * T
        counts = Counter(recent)
        train_win = counts["won"] / max(1, len(recent))
        row = {"update": update, "steps": steps, "seconds": round(time.perf_counter() - start, 1),
               "train_win_rate": round(train_win, 4), "entropy": round(ent.item(), 3),
               "train_outcomes": dict(counts.most_common(4))}
        if update % cfg.eval_every == 0 or update == updates:
            ev = evaluate(net, cfg.scenario, cfg.eval_games, cfg.eval_seed)
            row["eval"] = ev
            meta = {"config": asdict(cfg), "steps": steps, "eval": ev}
            save_model(net, out / "last.pt", meta)
            if ev["win_rate"] >= best:
                best = ev["win_rate"]
                save_model(net, out / "best.pt", meta)
        history.append(row)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        log(json.dumps(row, ensure_ascii=False))
    vec.close()
    return net


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train a Sky Team agent by self-play (PPO).")
    for name, value in asdict(TrainConfig()).items():
        parser.add_argument(f"--{name.replace('_', '-')}", type=type(value), default=value)
    args = parser.parse_args(argv)
    train(TrainConfig(**vars(args)))


if __name__ == "__main__":
    main()
