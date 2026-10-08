"""Final round and landing (MB p.10-11).

The scripted game in ``scripts.WINNING_ROUNDS`` clears the 3 airplanes in round 1,
deploys all gear and flaps and two brakes, reaches the airport in round 5, holds in
round 6 and lands in round 7 with speed 3 against a brake limit of 4.
"""

import pytest

from conftest import C, P, make_game, place, start_placement
from scripts import WINNING_ROUNDS, play_rounds
from skyteam.core.enums import GameStatus, LossReason


def _game_at_final_round():
    game = make_game()
    play_rounds(game, WINNING_ROUNDS[:6])
    assert game.state.round == 7 and game.state.status is GameStatus.IN_PROGRESS
    return game


@pytest.mark.rule("R-LND-05")
def test_scripted_game_lands():
    game = make_game()
    play_rounds(game, WINNING_ROUNDS)
    assert game.get_result() == (GameStatus.WON, "landed")


@pytest.mark.rule("R-ENG-04")
def test_final_round_engines_do_not_move_plane():
    game = _game_at_final_round()
    play_rounds(game, WINNING_ROUNDS[6:])
    assert game.state.approach_position == 5


@pytest.mark.rule("R-LND-04")
def test_landing_too_fast():
    game = _game_at_final_round()
    start_placement(game, [1, 1, 2, 4], [1, 1, 2, 4])
    for player, slot, value in [(P, "radio.pilot", 1), (C, "radio.copilot.1", 1), (P, "concentration.1", 1),
                                (C, "concentration.2", 1), (P, "axis.pilot", 2), (C, "axis.copilot", 2),
                                (P, "engines.pilot", 4), (C, "engines.copilot", 4)]:
        place(game, player, slot, value)
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_SPEED.value)


@pytest.mark.rule("R-BRK-07")
def test_brake_after_engines_does_not_count():
    game = _game_at_final_round()
    game.state.switches["brakes.2"] = False   # only one brake deployed: limit 2
    game.state.brakes_deployed = 1
    start_placement(game, [2, 1, 4, 1], [1, 1, 2, 2])
    for player, slot, value in [(P, "axis.pilot", 2), (C, "axis.copilot", 2), (P, "engines.pilot", 1),
                                (C, "engines.copilot", 2),     # speed 3 > limit 2 at this moment
                                (P, "brakes.2", 4),             # limit becomes 4, too late
                                (C, "radio.copilot.1", 1), (P, "radio.pilot", 1), (C, "concentration.1", 1)]:
        place(game, player, slot, value)
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_SPEED.value)


@pytest.mark.rule("R-LND-03")
def test_landing_with_tilted_axis():
    game = _game_at_final_round()
    start_placement(game, [1, 1, 2, 1], [1, 1, 3, 1])
    for player, slot, value in [(P, "radio.pilot", 1), (C, "radio.copilot.1", 1), (P, "concentration.1", 1),
                                (C, "concentration.2", 1), (P, "axis.pilot", 2), (C, "axis.copilot", 3),
                                (P, "engines.pilot", 1), (C, "engines.copilot", 1)]:
        place(game, player, slot, value)
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_AXIS.value)


@pytest.mark.rule("R-LND-01")
def test_landing_with_traffic_left():
    game = _game_at_final_round()
    game.state.traffic[2] = 1
    game.state.plane_supply -= 1
    play_rounds(game, WINNING_ROUNDS[6:])
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_TRAFFIC.value)


@pytest.mark.rule("R-LND-02")
def test_landing_without_all_flaps():
    game = _game_at_final_round()
    game.state.switches["flaps.4"] = False
    game.state.aero_orange -= 1
    play_rounds(game, WINNING_ROUNDS[6:])
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_CONFIGURATION.value)
