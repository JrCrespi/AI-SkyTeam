"""Headless simulation: ``python -m skyteam.simulate --scenario YUL_green --games 10000 --seed 42``.

Imports nothing from the UI. Runs the engine with undo snapshots disabled.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from skyteam.core.actions import Action
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

Policy = Callable[[SkyTeamGame, list[Action], random.Random], Action]


def random_policy(game: SkyTeamGame, legal: list[Action], rng: random.Random) -> Action:
    return rng.choice(legal)


POLICIES: dict[str, Policy] = {"random": random_policy}


@dataclass(slots=True)
class SimulationReport:
    scenario: str
    games: int
    seed: int
    policy: str
    seconds: float
    steps: int
    outcomes: dict[str, int]

    @property
    def games_per_second(self) -> float:
        return self.games / self.seconds if self.seconds else float("inf")

    @property
    def steps_per_second(self) -> float:
        return self.steps / self.seconds if self.seconds else float("inf")

    def to_dict(self) -> dict:
        return {"scenario": self.scenario, "games": self.games, "seed": self.seed, "policy": self.policy,
                "seconds": round(self.seconds, 3), "steps": self.steps,
                "games_per_second": round(self.games_per_second, 1),
                "steps_per_second": round(self.steps_per_second, 1), "outcomes": self.outcomes}


def simulate(scenario: str, games: int, seed: int = 0, policy: str = "random") -> SimulationReport:
    """Play ``games`` games; game ``i`` uses engine seed ``seed + i`` (each one reproducible alone)."""
    sc = load_scenario(scenario)
    choose = POLICIES[policy]
    outcomes: Counter[str] = Counter()
    steps = 0
    start = time.perf_counter()
    for i in range(games):
        game = SkyTeamGame(sc, config=GameConfig(keep_undo=False))
        game.reset(seed + i)
        rng = random.Random(seed + i)
        while not game.is_terminal():
            game.step(choose(game, game.get_legal_actions(), rng))
            steps += 1
        status, reason = game.get_result()
        outcomes[f"{status.value}:{reason}"] += 1
    return SimulationReport(scenario, games, seed, policy, time.perf_counter() - start, steps,
                            dict(sorted(outcomes.items(), key=lambda kv: -kv[1])))


def benchmark_simulations(games: int = 10000, scenario: str = "YUL_green", seed: int = 0) -> SimulationReport:
    return simulate(scenario, games, seed)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Sky Team games without any interface.")
    parser.add_argument("--scenario", default="YUL_green")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="random")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    report = simulate(args.scenario, args.games, args.seed, args.policy)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return
    print(f"{report.games} games of {report.scenario} ({report.policy} policy, seed {report.seed})")
    print(f"{report.seconds:.2f}s  {report.games_per_second:.0f} games/s  {report.steps_per_second:.0f} steps/s")
    for outcome, n in report.outcomes.items():
        print(f"  {outcome:40s} {n:6d}  {100 * n / report.games:5.1f}%")


if __name__ == "__main__":
    main()
