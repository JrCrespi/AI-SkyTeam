import json
import random

from conftest import make_game, random_playout
from scripts import WINNING_ROUNDS, play_rounds
from skyteam.core.actions import action_from_dict
from skyteam.core.state import GameState


def test_state_round_trip_through_json(game):
    play_rounds(game, WINNING_ROUNDS[:3])
    data = json.loads(json.dumps(game.save_state()))
    assert GameState.from_dict(data) == game.state


def test_load_state_restores_snapshot(game):
    play_rounds(game, WINNING_ROUNDS[:2])
    snap = game.save_state()
    play_rounds(game, WINNING_ROUNDS[2:4])
    game.load_state(snap)
    assert game.state.round == 3


def test_clone_is_independent(game):
    play_rounds(game, WINNING_ROUNDS[:2])
    other = game.clone()
    other.state.axis = 2
    other.state.traffic[0] = 5
    assert game.state.axis == 0 and game.state.traffic[0] == 0


def test_undo_restores_previous_state(game):
    before = game.state.copy()
    n_events = len(game.events)
    action = game.get_legal_actions()[0]
    game.step(action)
    game.undo_action()
    assert game.state == before
    assert len(game.events) == n_events


def test_same_seed_and_actions_reproduce_the_game():
    first = make_game(seed=12345, debug=False)
    random_playout(first, random.Random(1))
    replay = make_game(seed=12345, debug=False)
    for action in first.actions:
        replay.step(action_from_dict(json.loads(json.dumps(action.to_dict()))))
    assert replay.state == first.state
    assert [e.to_dict() for e in replay.events] == [e.to_dict() for e in first.events]


def test_different_seeds_give_different_dice():
    a, b = make_game(seed=1), make_game(seed=2)
    for g in (a, b):
        while g.state.phase.value == "strategy":
            g.step(g.get_legal_actions()[0])
    assert [d.value for d in a.state.dice] != [d.value for d in b.state.dice]
