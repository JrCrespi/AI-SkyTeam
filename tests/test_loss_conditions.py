"""One test per base-game loss condition. Placement-time losses live in their mechanic tests too."""

import pytest

from conftest import C, P, make_game, place, start_placement
from scripts import WINNING_ROUNDS, play_rounds
from skyteam.core.enums import GamePhase, GameStatus, LossReason


@pytest.mark.rule("R-LOSS-04")
def test_mandatory_slots_empty_at_end_of_round(game):
    start_placement(game, [1, 1, 1, 1], [1, 1, 1, 1])
    for player, slot in [(P, "radio.pilot"), (C, "radio.copilot.1"), (P, "concentration.1"),
                         (C, "concentration.2"), (P, "axis.pilot"), (C, "axis.copilot"),
                         (P, "engines.pilot"), (C, "radio.copilot.2")]:
        place(game, player, slot, 1)
    assert game.get_result() == (GameStatus.LOST, LossReason.MANDATORY_SLOT_EMPTY.value)
    assert game.state.phase is GamePhase.GAME_OVER


@pytest.mark.rule("R-LOSS-05")
def test_out_of_altitude_before_airport():
    game = make_game()
    play_rounds(game, WINNING_ROUNDS[:4])            # plane on space 4 after round 4
    pilot_first = [(P, "radio.pilot", 1), (C, "radio.copilot.1", 1), (P, "concentration.1", 1),
                   (C, "radio.copilot.2", 1), (P, "axis.pilot", 3), (C, "axis.copilot", 3),
                   (P, "engines.pilot", 3), (C, "engines.copilot", 3)]
    copilot_first = [(C, "radio.copilot.1", 1), (P, "radio.pilot", 1), (C, "radio.copilot.2", 1),
                     (P, "concentration.1", 1), (C, "axis.copilot", 3), (P, "axis.pilot", 3),
                     (C, "engines.copilot", 3), (P, "engines.pilot", 3)]
    dice = [1, 1, 3, 3]
    play_rounds(game, [(dice, dice, pilot_first), (dice, dice, copilot_first)])  # speed 6 <= blue 7: hold
    assert game.state.approach_position == 4
    assert game.get_result() == (GameStatus.LOST, LossReason.CRASH_BEFORE_AIRPORT.value)


def test_terminal_game_accepts_no_actions(game):
    game.state.axis = 2
    start_placement(game, [1, 1, 1, 1], [2, 1, 1, 1])
    place(game, P, "axis.pilot", 1)
    place(game, C, "axis.copilot", 2)
    assert game.is_terminal()
    assert game.get_legal_actions(P) == [] and game.get_legal_actions(C) == []
    assert game.current_player is None
