import pytest

from conftest import C, P, place, start_placement
from skyteam.core.enums import GameStatus, LossReason


@pytest.mark.rule("R-APP-03")
def test_moving_onto_traffic_is_allowed(game):
    # TEST track: one airplane on space 1.
    start_placement(game, [3, 1, 1, 1], [4, 1, 1, 1])
    place(game, P, "engines.pilot", 3)
    place(game, C, "engines.copilot", 4)
    assert game.state.approach_position == 1
    assert game.state.status is GameStatus.IN_PROGRESS


@pytest.mark.rule("R-LOSS-02")
def test_collision_when_leaving_space_with_traffic(game):
    game.state.approach_position = 1   # airplane on space 1
    start_placement(game, [3, 1, 1, 1], [4, 1, 1, 1])
    place(game, P, "engines.pilot", 3)
    place(game, C, "engines.copilot", 4)
    assert game.state.terminal_reason == LossReason.COLLISION.value


@pytest.mark.rule("R-APP-04")
def test_advance_two_collides_on_second_step(game):
    # Start on 0, traffic on 1: the first step lands on 1, the second step must leave it.
    start_placement(game, [5, 1, 1, 1], [5, 1, 1, 1])
    place(game, P, "engines.pilot", 5)
    place(game, C, "engines.copilot", 5)
    assert game.state.terminal_reason == LossReason.COLLISION.value
    assert game.state.approach_position == 1


@pytest.mark.rule("R-LOSS-03")
def test_overshoot(game):
    game.state.approach_position = 5
    start_placement(game, [3, 1, 1, 1], [4, 1, 1, 1])
    place(game, P, "engines.pilot", 3)
    place(game, C, "engines.copilot", 4)
    assert game.state.terminal_reason == LossReason.OVERSHOOT.value


@pytest.mark.rule("R-APP-06")
def test_holding_pattern_at_airport_with_low_speed(game):
    game.state.approach_position = 5
    start_placement(game, [2, 1, 1, 1], [2, 1, 1, 1])
    place(game, P, "engines.pilot", 2)
    place(game, C, "engines.copilot", 2)
    assert game.state.status is GameStatus.IN_PROGRESS
    assert game.state.approach_position == 5
