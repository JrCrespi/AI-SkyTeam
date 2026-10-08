"""Shared helpers for the test-suite.

Tests use a synthetic scenario (``tests/fixtures``) because the official approach tracks
have not been transcribed yet. Debug mode lets a test fix dice values after the roll.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from skyteam.core.actions import (
    ConfirmStrategyAction,
    PassRerollAction,
    PlaceDieAction,
)
from skyteam.core.enums import DecisionKind, GamePhase, Player
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

FIXTURES = Path(__file__).parent / "fixtures"
P, C = Player.PILOT, Player.COPILOT


def make_game(seed: int = 0, scenario: str = "TEST_basic", debug: bool = True) -> SkyTeamGame:
    game = SkyTeamGame(load_scenario(scenario, (FIXTURES,)), config=GameConfig(debug=debug))
    game.reset(seed)
    return game


def pass_reroll_windows(game: SkyTeamGame) -> None:
    while game.state.pending and game.state.pending[0].kind is DecisionKind.REROLL_WINDOW:
        game.step(PassRerollAction(game.state.pending[0].player))


def start_placement(game: SkyTeamGame, pilot: list[int], copilot: list[int]) -> None:
    """Finish the briefing and force the rolled dice to the given values."""
    assert game.state.phase is GamePhase.STRATEGY
    while game.state.phase is GamePhase.STRATEGY:
        game.step(ConfirmStrategyAction(game.current_player))
    values = {d.die_id: v for d, v in zip(game.state.dice_of(P), pilot)}
    values |= {d.die_id: v for d, v in zip(game.state.dice_of(C), copilot)}
    game.debug_set_dice(values)
    pass_reroll_windows(game)


def place(game: SkyTeamGame, player: Player, slot: str, value: int, coffee: int = 0):
    """Place a hidden die of ``player`` currently showing ``value``."""
    pass_reroll_windows(game)
    die = next(d for d in game.state.hidden_dice(player) if d.value == value)
    result = game.step(PlaceDieAction(player, die.die_id, slot, coffee))
    pass_reroll_windows(game)
    return result


def play_round(game: SkyTeamGame, pilot: list[int], copilot: list[int],
               moves: list[tuple[Player, str, int]]) -> None:
    start_placement(game, pilot, copilot)
    for player, slot, value in moves:
        if game.is_terminal():
            return
        place(game, player, slot, value)


def random_playout(game: SkyTeamGame, rng: random.Random, max_steps: int = 1000) -> int:
    steps = 0
    while not game.is_terminal():
        game.step(rng.choice(game.get_legal_actions()))
        steps += 1
        assert steps < max_steps, "game did not terminate"
    return steps


@pytest.fixture
def game() -> SkyTeamGame:
    return make_game()
