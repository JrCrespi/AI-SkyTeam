"""Terminal two-player mode (``python -m skyteam.play``)."""

from __future__ import annotations

import random

from skyteam.core.enums import Player
from skyteam.core.game import SkyTeamGame
from skyteam.play import play, render
from skyteam.scenarios.loader import load_scenario


def scripted(seed: int):
    rng = random.Random(seed)
    return lambda text: "" if "Enter" in text else str(rng.randint(1, 4))


def test_game_runs_to_the_end_with_menu_input(capsys):
    for seed in range(5):
        game = play(seed=seed, prompt=scripted(seed))
        assert game.is_terminal()
    out = capsys.readouterr().out
    assert out.count("Fim de jogo") + out.count("POUSO PERFEITO") == 5


def test_render_shows_only_own_dice():
    game = SkyTeamGame(load_scenario("YUL_green"))
    game.reset(1)
    while game.state.phase.value == "strategy":
        game.step(game.get_legal_actions()[0])
    pilot_view = render(game, Player.PILOT)
    own = sorted(d.value for d in game.state.dice_of(Player.PILOT))
    assert f"Seus dados: {own}" in pilot_view
    assert "Dados escondidos do parceiro: 4" in pilot_view
