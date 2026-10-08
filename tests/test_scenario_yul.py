"""Etapa 6: YUL Montréal-Trudeau (tutorial scenario) end to end.

Track in play order: traffic [0, 0, 1, 2, 1, 3, 2], the airport is index 6 and holds 2 airplanes.
The scripted game clears all 9 airplanes with the Radio, advances exactly one space in rounds 1-6,
deploys all gear and flaps plus two brakes, and lands in round 7 with speed 3 against a limit of 4.
"""

import random

import pytest

from conftest import C, P, place, start_placement
from scripts import play_rounds
from skyteam.core.enums import GameStatus, LossReason
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

YUL_WIN = [
    # R1 6000 ft, pilot first, pos 0 -> 1: radio 3 -> space 2, radio 4 x2 -> space 3
    ([3, 4, 3, 3], [4, 4, 3, 3], [
        (P, "radio.pilot", 3), (C, "radio.copilot.1", 4), (P, "gear.2", 4), (C, "radio.copilot.2", 4),
        (P, "axis.pilot", 3), (C, "axis.copilot", 3), (P, "engines.pilot", 3), (C, "engines.copilot", 3)]),
    # R2 5000 ft, copilot first, pos 1 -> 2: clear space 4 and two of space 5
    ([5, 2, 3, 4], [4, 5, 3, 4], [
        (C, "radio.copilot.1", 4), (P, "radio.pilot", 5), (C, "radio.copilot.2", 5), (P, "gear.1", 2),
        (C, "axis.copilot", 3), (P, "axis.pilot", 3), (C, "engines.copilot", 4), (P, "engines.pilot", 4)]),
    # R3 4000 ft, pilot first, pos 2 -> 3: last gear, first brake, two flaps
    ([6, 2, 3, 4], [2, 3, 3, 4], [
        (P, "gear.3", 6), (C, "flaps.1", 2), (P, "brakes.1", 2), (C, "flaps.2", 3),
        (P, "axis.pilot", 3), (C, "axis.copilot", 3), (P, "engines.pilot", 4), (C, "engines.copilot", 4)]),
    # R4 3000 ft, copilot first, pos 3 -> 4: last flaps, second brake, clear space 5
    ([3, 4, 3, 4], [4, 6, 3, 4], [
        (C, "flaps.3", 4), (P, "radio.pilot", 3), (C, "flaps.4", 6), (P, "brakes.2", 4),
        (C, "axis.copilot", 3), (P, "axis.pilot", 3), (C, "engines.copilot", 4), (P, "engines.pilot", 4)]),
    # R5 2000 ft, pilot first, pos 4 -> 5: clear both airplanes on the airport
    ([1, 1, 3, 4], [3, 3, 3, 4], [
        (P, "concentration.1", 1), (C, "radio.copilot.1", 3), (P, "concentration.2", 1), (C, "radio.copilot.2", 3),
        (P, "axis.pilot", 3), (C, "axis.copilot", 3), (P, "engines.pilot", 4), (C, "engines.copilot", 4)]),
    # R6 1000 ft, copilot first, pos 5 -> 6 (airport)
    ([1, 1, 3, 4], [1, 1, 3, 4], [
        (C, "radio.copilot.1", 1), (P, "radio.pilot", 1), (C, "concentration.2", 1), (P, "concentration.1", 1),
        (C, "axis.copilot", 3), (P, "axis.pilot", 3), (C, "engines.copilot", 4), (P, "engines.pilot", 4)]),
    # R7 landing, pilot first: speed 3 <= 4
    ([1, 1, 2, 1], [1, 1, 2, 2], [
        (P, "radio.pilot", 1), (C, "radio.copilot.1", 1), (P, "concentration.1", 1), (C, "concentration.2", 1),
        (P, "axis.pilot", 2), (C, "axis.copilot", 2), (P, "engines.pilot", 1), (C, "engines.copilot", 2)]),
]


def yul_game(seed: int = 0, debug: bool = True) -> SkyTeamGame:
    game = SkyTeamGame(load_scenario("YUL_green"), config=GameConfig(debug=debug))
    game.reset(seed)
    return game


@pytest.mark.rule("R-SET-07")
def test_yul_setup():
    game = yul_game()
    assert game.scenario.verified
    assert game.state.traffic == [0, 0, 1, 2, 1, 3, 2]
    assert game.state.plane_supply == 12 - 9
    assert game.state.approach_position == 0
    assert (game.state.aero_blue, game.state.aero_orange, game.state.brakes_deployed) == (4, 8, 0)


def test_yul_scripted_landing():
    game = yul_game()
    play_rounds(game, YUL_WIN)
    assert game.get_result() == (GameStatus.WON, "landed")
    assert sum(game.state.traffic) == 0 and game.state.round == 7


@pytest.mark.rule("R-LND-01")
def test_yul_airport_traffic_must_be_cleared():
    game = yul_game()
    skip_airport_clearing = YUL_WIN[4][2].copy()
    skip_airport_clearing[1] = (C, "radio.copilot.1", 1)   # radio on the current space instead
    skip_airport_clearing[3] = (C, "radio.copilot.2", 1)
    final_without_radio = ([3, 1, 2, 1], [3, 1, 2, 2], [
        (P, "radio.pilot", 3), (C, "radio.copilot.1", 3), (P, "concentration.1", 1), (C, "concentration.2", 1),
        (P, "axis.pilot", 2), (C, "axis.copilot", 2), (P, "engines.pilot", 1), (C, "engines.copilot", 2)])
    rounds = (YUL_WIN[:4] + [([1, 1, 3, 4], [1, 1, 3, 4], skip_airport_clearing)] + [YUL_WIN[5]]
              + [final_without_radio])
    play_rounds(game, rounds)
    assert game.state.traffic[6] == 2
    assert game.get_result() == (GameStatus.LOST, LossReason.LANDING_TRAFFIC.value)


@pytest.mark.rule("R-LOSS-02")
def test_yul_collision_without_radio():
    game = yul_game()
    play_rounds(game, YUL_WIN[:1])                 # pos 1; space 2 is clear, spaces 4 and 5 are not
    play_rounds(game, YUL_WIN[1:4])                # pos 4 with space 5 cleared in round 4
    game.state.traffic[4] = 1                      # an airplane on the Current Position
    game.state.plane_supply -= 1
    start_placement(game, [1, 1, 3, 4], [3, 3, 3, 4])
    for player, slot, value in [(P, "axis.pilot", 3), (C, "axis.copilot", 3),
                                (P, "engines.pilot", 4), (C, "engines.copilot", 4)]:
        place(game, player, slot, value)
    assert game.get_result() == (GameStatus.LOST, LossReason.COLLISION.value)


@pytest.mark.parametrize("seed", range(100))
def test_yul_random_games(seed):
    game = yul_game(seed=seed)
    rng = random.Random(seed)
    steps = 0
    while not game.is_terminal():
        game.step(rng.choice(game.get_legal_actions()))
        steps += 1
        assert steps < 1000
    assert game.state.status is not GameStatus.IN_PROGRESS
