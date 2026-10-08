import pytest

from conftest import C, P, place, start_placement
from skyteam.mechanics.engines import advance_for_speed


@pytest.mark.rule("R-ENG-03")
@pytest.mark.parametrize("speed,steps", [(2, 0), (4, 0), (5, 1), (7, 1), (8, 1), (9, 2), (10, 2), (12, 2)])
def test_advance_with_initial_markers(speed, steps):
    # Markers between 4/5 and 8/9 (R-SET-02); MB p.6 examples: 4 -> 0, 7 -> 1, 10 -> 2.
    assert advance_for_speed(speed, 4, 8) == steps


@pytest.mark.rule("R-GEA-03")
def test_moving_blue_marker_changes_effect_of_speed():
    # MB p.7: after moving the blue marker forward, a speed of 5 advances 0 instead of 1.
    assert advance_for_speed(5, 4, 8) == 1
    assert advance_for_speed(5, 5, 8) == 0


@pytest.mark.rule("R-ENG-02")
def test_engines_move_plane_on_second_die(game):
    start_placement(game, [3, 1, 1, 1], [4, 1, 1, 1])
    place(game, P, "engines.pilot", 3)
    assert game.state.approach_position == 0
    place(game, C, "engines.copilot", 4)
    assert game.state.last_speed == 7
    assert game.state.approach_position == 1
