"""Scripted games on the synthetic TEST track (traffic [0,1,0,2,0,0], airport at 5)."""

from __future__ import annotations

from conftest import C, P, play_round

# (pilot dice, copilot dice, moves) per round; derivation in tests/test_landing.py docstring.
WINNING_ROUNDS = [
    # R1 6000 ft, pilot first: clear all traffic, advance 1 (speed 6, blue 5)
    ([4, 4, 3, 3], [2, 4, 3, 3], [
        (P, "radio.pilot", 4), (C, "radio.copilot.1", 2), (P, "gear.2", 4), (C, "radio.copilot.2", 4),
        (P, "axis.pilot", 3), (C, "axis.copilot", 3), (P, "engines.pilot", 3), (C, "engines.copilot", 3)]),
    # R2 5000 ft, copilot first: advance 1 (speed 8, blue 6, orange 9)
    ([2, 2, 4, 4], [2, 6, 4, 4], [
        (C, "flaps.1", 2), (P, "gear.1", 2), (C, "concentration.1", 6), (P, "brakes.1", 2),
        (C, "axis.copilot", 4), (P, "axis.pilot", 4), (C, "engines.copilot", 4), (P, "engines.pilot", 4)]),
    # R3 4000 ft, pilot first: advance 1 (speed 8, blue 7, orange 10)
    ([6, 4, 4, 4], [3, 1, 4, 4], [
        (P, "gear.3", 6), (C, "flaps.2", 3), (P, "brakes.2", 4), (C, "concentration.1", 1),
        (P, "axis.pilot", 4), (C, "axis.copilot", 4), (P, "engines.pilot", 4), (C, "engines.copilot", 4)]),
    # R4 3000 ft, copilot first: advance 1 (speed 8, orange 11)
    ([6, 1, 5, 4], [5, 6, 5, 4], [
        (C, "flaps.3", 5), (P, "radio.pilot", 6), (C, "radio.copilot.1", 6), (P, "concentration.1", 1),
        (C, "axis.copilot", 5), (P, "axis.pilot", 5), (C, "engines.copilot", 4), (P, "engines.pilot", 4)]),
    # R5 2000 ft, pilot first: advance 1 onto the airport (speed 8, orange 12)
    ([1, 1, 2, 4], [6, 1, 2, 4], [
        (P, "radio.pilot", 1), (C, "flaps.4", 6), (P, "concentration.1", 1), (C, "concentration.2", 1),
        (P, "axis.pilot", 2), (C, "axis.copilot", 2), (P, "engines.pilot", 4), (C, "engines.copilot", 4)]),
    # R6 1000 ft, copilot first: holding pattern, advance 0 (speed 6 <= blue 7)
    ([1, 1, 3, 3], [1, 1, 3, 3], [
        (C, "radio.copilot.1", 1), (P, "radio.pilot", 1), (C, "radio.copilot.2", 1), (P, "concentration.1", 1),
        (C, "axis.copilot", 3), (P, "axis.pilot", 3), (C, "engines.copilot", 3), (P, "engines.pilot", 3)]),
    # R7 landing, pilot first: speed 3 <= brake limit 4, axis level
    ([1, 1, 2, 1], [1, 1, 2, 2], [
        (P, "radio.pilot", 1), (C, "radio.copilot.1", 1), (P, "concentration.1", 1), (C, "concentration.2", 1),
        (P, "axis.pilot", 2), (C, "axis.copilot", 2), (P, "engines.pilot", 1), (C, "engines.copilot", 2)]),
]


def play_rounds(game, rounds) -> None:
    for pilot, copilot, moves in rounds:
        if game.is_terminal():
            return
        play_round(game, pilot, copilot, moves)
