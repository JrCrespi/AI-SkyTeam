"""Property-style checks over many random games (strict mode validates after every action)."""

import random

import pytest

from conftest import make_game, random_playout
from skyteam.core.enums import GameStatus


@pytest.mark.parametrize("seed", range(150))
def test_random_games_keep_invariants_and_terminate(seed):
    game = make_game(seed=seed)            # debug=True implies validate_state after each step
    random_playout(game, random.Random(seed))
    assert game.state.status in (GameStatus.WON, GameStatus.LOST)
    assert game.state.terminal_reason


@pytest.mark.parametrize("seed", range(20))
def test_every_legal_action_is_accepted(seed):
    game = make_game(seed=seed)
    rng = random.Random(seed)
    while not game.is_terminal():
        legal = game.get_legal_actions()
        assert legal, "a non-terminal state must offer actions to the current player"
        for action in legal:
            assert game.is_action_legal(action)
        game.step(rng.choice(legal))


@pytest.mark.rule("R-TURN-10")
@pytest.mark.parametrize("seed", range(200))
def test_base_panel_never_blocks_a_player(seed):
    """P2 cannot happen with the base panel (see docs/architecture.md)."""
    from skyteam.core.actions import DiscardDieAction
    game = make_game(seed=seed, debug=False)
    rng = random.Random(seed)
    while not game.is_terminal():
        legal = game.get_legal_actions()
        assert not any(isinstance(a, DiscardDieAction) for a in legal)
        game.step(rng.choice(legal))
