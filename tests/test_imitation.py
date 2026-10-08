"""Learning from recorded games (needs torch; skipped otherwise)."""

from __future__ import annotations

import random

import pytest

torch = pytest.importorskip("torch")

from skyteam.ai.imitation import accuracy, build_dataset, load_replays, main, train_imitation  # noqa: E402
from skyteam.ai.ppo import TrainConfig, load_model, train  # noqa: E402
from skyteam.core.game import SkyTeamGame  # noqa: E402
from skyteam.replay import save_finished_game  # noqa: E402
from skyteam.scenarios.loader import load_scenario  # noqa: E402



def record_games(directory, n: int) -> None:
    for seed in range(n):
        game = SkyTeamGame(load_scenario("YUL_green"))
        game.reset(seed)
        rng = random.Random(seed)
        while not game.is_terminal():
            game.step(rng.choice(game.get_legal_actions()))
        save_finished_game(game, directory)


def test_dataset_rebuilds_every_move(tmp_path):
    record_games(tmp_path, 4)
    replays = load_replays(tmp_path)
    data = build_dataset(replays)
    assert data.games == 4 and len(data) == sum(len(r.actions) for r in replays)
    assert all(data.mask[i, data.action[i]] for i in range(len(data)))
    assert set(data.outcome.tolist()) <= {1.0, -1.0}


def test_imitation_learns_the_recorded_moves(tmp_path):
    record_games(tmp_path, 6)
    data = build_dataset(load_replays(tmp_path))
    before = accuracy(train_imitation(data, epochs=0, hidden=64), data)
    after = accuracy(train_imitation(data, epochs=60, hidden=64), data)
    assert after > before and after > 0.5


def test_cli_and_self_play_can_start_from_the_imitation_model(tmp_path):
    record_games(tmp_path / "games", 3)
    model = tmp_path / "bc.pt"
    main(["--data", str(tmp_path / "games"), "--out", str(model), "--epochs", "2"])
    _, meta = load_model(model)
    assert meta["imitation"]["games"] == 3
    cfg = TrainConfig(steps=2 * 16, envs=2, rollout=16, minibatch=16, eval_every=1, eval_games=2,
                      workers=1, init=str(model), out=str(tmp_path / "run"))
    train(cfg, log=lambda _: None)
    assert (tmp_path / "run" / "best.pt").exists()
