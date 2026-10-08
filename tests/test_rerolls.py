import pytest

from conftest import C, P
from skyteam.core.actions import (
    ChooseRerollAction,
    ConfirmStrategyAction,
    PassRerollAction,
    UseRerollAction,
)
from skyteam.core.enums import DecisionKind


def _to_placement(game):
    game.step(ConfirmStrategyAction(P))
    game.step(ConfirmStrategyAction(C))


@pytest.mark.rule("R-RER-01")
def test_first_round_collects_reroll_token(game):
    assert game.state.reroll_supply == 1
    assert game.state.altitude_rerolls[0] is False


@pytest.mark.rule("R-RER-02")
def test_non_active_player_gets_reroll_window(game):
    _to_placement(game)
    top = game.state.pending[0]
    assert top.kind is DecisionKind.REROLL_WINDOW and top.player is C
    assert game.current_player is C
    game.step(PassRerollAction(C))
    assert game.current_player is P
    assert UseRerollAction(P) in game.get_legal_actions(P)


@pytest.mark.rule("R-RER-03")
def test_reroll_lets_both_players_choose(game):
    _to_placement(game)
    game.step(UseRerollAction(C))
    assert game.state.reroll_supply == 0
    assert [(d.kind, d.player) for d in game.state.pending] == [
        (DecisionKind.REROLL_CHOICE, P), (DecisionKind.REROLL_CHOICE, C)]
    options = game.get_legal_actions(P)
    assert len(options) == 16                   # every subset of 4 hidden dice
    before = [d.value for d in game.state.dice_of(C)]
    game.step(ChooseRerollAction(P, (0, 1)))
    game.step(ChooseRerollAction(C, ()))
    assert [d.value for d in game.state.dice_of(C)] == before
    assert game.current_player is P and not game.state.pending


def test_cannot_reroll_partner_dice(game):
    _to_placement(game)
    game.step(UseRerollAction(C))
    assert not game.is_action_legal(ChooseRerollAction(P, (4,)))
