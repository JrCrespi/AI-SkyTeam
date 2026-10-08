import pytest

from conftest import C, P, place, start_placement
from skyteam.core.actions import PlaceDieAction
from skyteam.mechanics.brakes import max_landing_speed


@pytest.mark.rule("R-BRK-02")
def test_brakes_in_order(game):
    start_placement(game, [4, 2, 1, 1], [1, 1, 1, 1])
    die4 = next(d for d in game.state.hidden_dice(P) if d.value == 4)
    assert not game.is_action_legal(PlaceDieAction(P, die4.die_id, "brakes.2"))
    place(game, P, "brakes.1", 2)
    place(game, C, "concentration.1", 1)
    place(game, P, "brakes.2", 4)
    assert game.state.brakes_deployed == 2


@pytest.mark.rule("R-BRK-01")
def test_brake_requires_exact_value(game):
    start_placement(game, [3, 1, 1, 1], [1, 1, 1, 1])
    die3 = next(d for d in game.state.hidden_dice(P) if d.value == 3)
    assert not game.is_action_legal(PlaceDieAction(P, die3.die_id, "brakes.1"))


@pytest.mark.rule("R-BRK-05")
def test_brake_thresholds(game):
    expected = {0: 1, 1: 2, 2: 4, 3: 6}   # index 1 is TODO_RULE_VERIFICATION P10a
    for deployed, limit in expected.items():
        game.state.brakes_deployed = deployed
        assert max_landing_speed(game._ctx()) == limit
