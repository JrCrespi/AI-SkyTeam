import pytest

from conftest import C, P, place, start_placement
from skyteam.core.actions import PlaceDieAction
from skyteam.mechanics.concentration import coffee_change_allowed


@pytest.mark.rule("R-COF-02")
def test_concentration_gives_coffee_up_to_three(game):
    start_placement(game, [6, 6, 1, 1], [5, 5, 1, 1])
    place(game, P, "concentration.1", 6)
    place(game, C, "concentration.2", 5)
    place(game, P, "concentration.3", 6)
    assert game.state.coffee == 3


@pytest.mark.rule("R-COF-07")
def test_concentration_when_full_gives_nothing(game):
    game.state.coffee = 3
    start_placement(game, [6, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "concentration.1", 6)
    assert game.state.coffee == 3


@pytest.mark.rule("R-COF-03")
def test_coffee_changes_die_when_placing(game):
    # MB p.8 example: a 3 becomes a 1 with 2 coffee to clear the Current Position.
    game.state.coffee = 2
    game.state.traffic[0] = 1
    game.state.plane_supply -= 1
    start_placement(game, [3, 1, 1, 1], [1, 1, 1, 1])
    die = next(d for d in game.state.hidden_dice(P) if d.value == 3)
    game.step(PlaceDieAction(P, die.die_id, "radio.pilot", -2))
    assert game.state.coffee == 0
    assert die.value == 1
    assert game.state.traffic[0] == 0


@pytest.mark.rule("R-COF-06")
def test_coffee_limits():
    assert coffee_change_allowed(3, -2, coffee=2, max_per_die=3, sides=6)
    assert not coffee_change_allowed(3, -2, coffee=1, max_per_die=3, sides=6)   # not enough tokens
    assert not coffee_change_allowed(1, -1, coffee=3, max_per_die=3, sides=6)   # no wrap to 6
    assert not coffee_change_allowed(6, +1, coffee=3, max_per_die=3, sides=6)   # no wrap to 1


@pytest.mark.rule("R-COF-04")
def test_any_player_uses_shared_coffee(game):
    game.state.coffee = 1
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    place(game, P, "concentration.1", 1)
    die = game.state.hidden_dice(C)[0]
    assert game.is_action_legal(PlaceDieAction(C, die.die_id, "radio.copilot.1", +1))
