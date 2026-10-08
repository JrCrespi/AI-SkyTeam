import pytest

from conftest import C, P, place, start_placement
from skyteam.core.actions import PlaceDieAction


@pytest.mark.rule("R-GEA-03")
def test_gear_moves_blue_marker(game):
    start_placement(game, [4, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "gear.2", 4)
    assert game.state.switches["gear.2"]
    assert game.state.aero_blue == 5           # between 5 and 6, MB p.7 example


@pytest.mark.rule("R-GEA-02")
def test_gear_order_does_not_matter(game):
    start_placement(game, [6, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "gear.3", 6)
    assert game.state.aero_blue == 5


@pytest.mark.rule("R-GEA-01")
def test_gear_value_constraint(game):
    start_placement(game, [3, 1, 1, 1], [1, 1, 1, 1])
    die = next(d for d in game.state.hidden_dice(P) if d.value == 3)
    assert not game.is_action_legal(PlaceDieAction(P, die.die_id, "gear.1"))
    assert game.is_action_legal(PlaceDieAction(P, die.die_id, "gear.2"))


@pytest.mark.rule("R-GEA-05")
def test_already_deployed_gear_has_no_effect(game):
    game.state.switches["gear.1"] = True
    game.state.aero_blue = 5
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "gear.1", 1)
    assert game.state.aero_blue == 5


@pytest.mark.rule("R-GEA-04")
def test_all_gear_puts_blue_marker_between_7_and_8(game):
    from scripts import WINNING_ROUNDS, play_rounds
    play_rounds(game, WINNING_ROUNDS[:3])
    assert game.state.aero_blue == 7
