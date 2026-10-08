"""Etapa 11: replays and the headless simulator."""

from __future__ import annotations

import json
import random

import pytest

from skyteam.core.game import SkyTeamGame
from skyteam.replay import GameReplay
from skyteam.scenarios.loader import load_scenario
from skyteam.simulate import main, simulate


def played_game(seed: int) -> SkyTeamGame:
    game = SkyTeamGame(load_scenario("YUL_green"))
    game.reset(seed)
    rng = random.Random(seed)
    while not game.is_terminal():
        game.step(rng.choice(game.get_legal_actions()))
    return game


@pytest.mark.parametrize("seed", range(5))
def test_replay_round_trip_reproduces_the_game(tmp_path, seed):
    game = played_game(seed)
    path = tmp_path / "game.json"
    GameReplay.from_game(game).save(path)
    again = GameReplay.load(path).run()
    assert again.state.to_dict() == game.state.to_dict()
    assert again.get_result() == game.get_result()


def test_replay_detects_divergence():
    replay = GameReplay.from_game(played_game(1))
    replay.result = {"status": "won" if replay.result["status"] != "won" else "lost",
                     "terminal_reason": "something else"}
    with pytest.raises(AssertionError):
        replay.run()


def test_replay_rejects_unknown_format():
    d = GameReplay.from_game(played_game(2)).to_dict()
    d["format"] = 99
    with pytest.raises(ValueError):
        GameReplay.from_dict(d)


def test_simulation_is_deterministic():
    a = simulate("YUL_green", 30, seed=5)
    b = simulate("YUL_green", 30, seed=5)
    assert a.outcomes == b.outcomes and a.steps == b.steps
    assert sum(a.outcomes.values()) == 30


def test_simulation_game_i_matches_a_single_game_with_seed_plus_i():
    many = simulate("YUL_green", 3, seed=10)
    singles = [simulate("YUL_green", 1, seed=10 + i) for i in range(3)]
    assert many.steps == sum(s.steps for s in singles)


def test_cli_prints_json(capsys):
    main(["--scenario", "YUL_green", "--games", "5", "--seed", "1", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["games"] == 5 and sum(report["outcomes"].values()) == 5
