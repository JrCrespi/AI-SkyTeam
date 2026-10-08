import pytest

from conftest import C, P, make_game, place, start_placement
from skyteam.core.actions import ConfirmStrategyAction, PlaceDieAction
from skyteam.core.enums import GamePhase
from skyteam.core.exceptions import IllegalActionError


def test_game_starts_in_strategy_with_pilot_first(game):
    assert game.state.phase is GamePhase.STRATEGY
    assert game.current_player is P
    assert all(d.value is None for d in game.state.dice)   # nothing rolled before the briefing


@pytest.mark.rule("R-COM-03")
def test_dice_are_rolled_after_both_players_confirm(game):
    game.step(ConfirmStrategyAction(P))
    assert game.state.phase is GamePhase.STRATEGY and game.current_player is C
    game.step(ConfirmStrategyAction(C))
    assert game.state.phase is GamePhase.DICE_PLACEMENT
    assert all(d.value is not None for d in game.state.dice)


def test_placement_is_illegal_during_strategy(game):
    action = PlaceDieAction(P, 0, "axis.pilot")
    assert not game.is_action_legal(action)
    assert "phase" in game.explain_illegal_action(action)[0]
    with pytest.raises(IllegalActionError):
        game.step(action)


@pytest.mark.rule("R-TURN-01")
def test_players_alternate(game):
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    assert game.current_player is P
    place(game, P, "concentration.1", 1)
    assert game.current_player is C
    assert game.get_legal_actions(P) == []
    place(game, C, "concentration.2", 1)
    assert game.current_player is P


@pytest.mark.rule("R-TURN-02")
def test_second_round_is_started_by_copilot():
    from scripts import WINNING_ROUNDS, play_rounds
    game = make_game()
    play_rounds(game, WINNING_ROUNDS[:1])
    assert game.state.round == 2 and game.current_player is C


@pytest.mark.rule("R-TURN-04")
def test_colour_constraint_message(game):
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    die = game.state.dice_of(P)[0]
    reasons = game.explain_illegal_action(PlaceDieAction(P, die.die_id, "flaps.1"))
    assert any("belongs to the Co-Pilot" in r for r in reasons)


def test_cannot_use_partner_die(game):
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    die = game.state.dice_of(C)[0]
    assert not game.is_action_legal(PlaceDieAction(P, die.die_id, "axis.pilot"))


@pytest.mark.rule("R-TURN-03")
def test_space_holds_one_die_per_round(game):
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    place(game, P, "concentration.1", 1)
    die = game.state.hidden_dice(C)[0]
    assert any("already has a die" in r
               for r in game.explain_illegal_action(PlaceDieAction(C, die.die_id, "concentration.1")))


def test_legal_actions_agree_with_validator(game):
    start_placement(game, [1, 2, 5, 6], [2, 3, 4, 6])
    legal = game.get_legal_actions(P)
    assert legal and all(game.is_action_legal(a) for a in legal)
    for die in game.state.hidden_dice(P):
        for slot in game.panel.slots:
            action = PlaceDieAction(P, die.die_id, slot.id)
            assert (action in legal) == game.is_action_legal(action)
