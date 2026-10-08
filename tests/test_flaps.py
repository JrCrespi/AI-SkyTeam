import pytest

from conftest import C, P, place, start_placement
from skyteam.core.actions import PlaceDieAction


@pytest.mark.rule("R-FLA-02")
def test_flaps_in_order(game):
    start_placement(game, [1, 1, 1, 1], [2, 3, 1, 1])
    place(game, P, "concentration.1", 1)
    die = next(d for d in game.state.hidden_dice(C) if d.value == 3)
    reasons = game.explain_illegal_action(PlaceDieAction(C, die.die_id, "flaps.2"))
    assert any("in order" in r for r in reasons)
    place(game, C, "flaps.1", 2)
    place(game, P, "concentration.2", 1)
    place(game, C, "flaps.2", 3)                # same round, right after flaps.1
    assert game.state.aero_orange == 10         # MB p.8 example: between 10 and 11


@pytest.mark.rule("R-FLA-03")
def test_flap_moves_orange_marker(game):
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "concentration.1", 1)
    place(game, C, "flaps.1", 1)
    assert game.state.aero_orange == 9


@pytest.mark.rule("R-FLA-04")
def test_all_flaps_put_orange_marker_past_12(game):
    from scripts import WINNING_ROUNDS, play_rounds
    play_rounds(game, WINNING_ROUNDS[:5])
    assert game.state.aero_orange == 12


@pytest.mark.rule("R-FLA-05")
def test_reusing_a_deployed_flap_has_no_effect(game):
    # TODO_RULE_VERIFICATION P9: allowed without effect, by analogy with the landing gear.
    game.state.switches["flaps.1"] = True
    game.state.aero_orange = 9
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "concentration.1", 1)
    place(game, C, "flaps.1", 1)
    assert game.state.aero_orange == 9
