"""Self-play training (needs torch; skipped otherwise)."""

from __future__ import annotations

import random

import pytest

torch = pytest.importorskip("torch")

from skyteam.ai.ppo import ModelAgent, TrainConfig, evaluate, load_model, train  # noqa: E402
from skyteam.ai.rewards import RoundSurvivedReward, training_reward  # noqa: E402
from skyteam.core.game import SkyTeamGame  # noqa: E402
from skyteam.core.enums import GameStatus  # noqa: E402
from skyteam.scenarios.loader import load_scenario  # noqa: E402
from skyteam.simulate import simulate  # noqa: E402


@pytest.fixture(scope="module")
def tiny_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    cfg = TrainConfig(steps=4 * 32 * 2, envs=4, rollout=32, minibatch=64, eval_every=1, eval_games=5,
                      hidden=32, workers=2, out=str(out))
    train(cfg, log=lambda _: None)
    return out


def test_training_writes_checkpoints_and_history(tiny_run):
    assert (tiny_run / "best.pt").exists() and (tiny_run / "last.pt").exists()
    assert (tiny_run / "history.json").exists()
    net, meta = load_model(tiny_run / "best.pt")
    assert meta["config"]["envs"] == 4 and "eval" in meta


def test_model_agent_only_plays_legal_actions(tiny_run):
    agent = ModelAgent(tiny_run / "best.pt")
    game = SkyTeamGame(load_scenario("YUL_green"))
    game.reset(3)
    while not game.is_terminal():
        action = agent.act(game, game.current_player)
        assert game.is_action_legal(action)
        game.step(action)


def test_model_agent_works_as_a_simulate_policy(tiny_run):
    report = simulate("YUL_green", 3, seed=0, policy=str(tiny_run / "best.pt"))
    assert sum(report.outcomes.values()) == 3


def test_evaluate_is_deterministic(tiny_run):
    net, _ = load_model(tiny_run / "best.pt")
    assert evaluate(net, "YUL_green", 5, 42) == evaluate(net, "YUL_green", 5, 42)


def test_round_survived_reward():
    game = SkyTeamGame(load_scenario("YUL_green"))
    game.reset(0)
    before = game.state.copy()
    after = before.copy()
    after.round += 1
    assert RoundSurvivedReward()(before, None, after) == 1.0
    after.status = GameStatus.LOST
    assert RoundSurvivedReward()(before, None, after) == 0.0
    assert training_reward(0.05).uses_before
