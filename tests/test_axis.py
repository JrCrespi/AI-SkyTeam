import pytest

from conftest import C, P, place, start_placement
from skyteam.core.enums import GameStatus, LossReason
from skyteam.mechanics.axis import axis_delta, is_spin


@pytest.mark.rule("R-AXI-02")
@pytest.mark.parametrize("pilot,copilot,delta", [(5, 3, -2), (3, 5, 2), (4, 4, 0), (6, 1, -5)])
def test_axis_turns_toward_higher_die(pilot, copilot, delta):
    assert axis_delta(pilot, copilot) == delta


@pytest.mark.rule("R-AXI-04")
def test_spin_threshold():
    assert not is_spin(2, 3) and not is_spin(-2, 3)
    assert is_spin(3, 3) and is_spin(-5, 3)


@pytest.mark.rule("R-AXI-02")
def test_axis_resolves_on_second_die(game):
    start_placement(game, [5, 1, 1, 1], [3, 1, 1, 1])
    place(game, P, "axis.pilot", 5)
    assert game.state.axis == 0
    place(game, C, "axis.copilot", 3)
    assert game.state.axis == -2   # two marks toward Isabelle (Pilot), MB p.5 example


@pytest.mark.rule("R-AXI-03")
def test_axis_is_not_reset_between_rounds(game):
    game.state.axis = 1
    start_placement(game, [3, 1, 1, 1], [3, 1, 1, 1])
    place(game, P, "axis.pilot", 3)
    place(game, C, "axis.copilot", 3)
    assert game.state.axis == 1


@pytest.mark.rule("R-LOSS-01")
def test_spin_loses_immediately(game):
    game.state.axis = 2
    start_placement(game, [1, 1, 1, 1], [2, 1, 1, 1])
    place(game, P, "axis.pilot", 1)
    place(game, C, "axis.copilot", 2)
    assert game.state.status is GameStatus.LOST
    assert game.state.terminal_reason == LossReason.AXIS_SPIN.value
