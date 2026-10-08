import pytest

from conftest import C, P, place, start_placement
from skyteam.mechanics.radio import target_space


@pytest.mark.rule("R-RAD-02")
def test_value_one_targets_current_position():
    assert target_space(3, 1) == 3
    assert target_space(3, 2) == 4


@pytest.mark.rule("R-RAD-02")
def test_radio_removes_one_airplane(game):
    start_placement(game, [4, 1, 1, 1], [4, 1, 1, 1])
    place(game, P, "radio.pilot", 4)          # space 3 has 2 airplanes
    assert game.state.traffic[3] == 1
    assert game.state.plane_supply == 12 - 2
    place(game, C, "radio.copilot.1", 4)
    assert game.state.traffic[3] == 0


@pytest.mark.rule("R-RAD-03")
def test_radio_without_airplane_has_no_effect(game):
    start_placement(game, [1, 1, 1, 1], [6, 1, 1, 1])
    before = list(game.state.traffic)
    place(game, P, "radio.pilot", 1)
    place(game, C, "radio.copilot.1", 6)       # beyond the airport (R-RAD-04)
    assert game.state.traffic == before


@pytest.mark.rule("R-RAD-01")
def test_pilot_cannot_use_copilot_radio(game):
    from skyteam.core.actions import PlaceDieAction
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    assert not game.is_action_legal(PlaceDieAction(P, 0, "radio.copilot.1"))
