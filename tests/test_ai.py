"""Etapa 10: action space, action mask, vector observation, rewards and the environment."""

from __future__ import annotations

import random

import pytest

from skyteam.ai.action_mask import action_mask
from skyteam.ai.action_space import ActionSpace
from skyteam.ai.environment import SkyTeamEnv
from skyteam.ai.observation import vector_layout, vector_observation, vector_size
from skyteam.ai.rewards import CompositeReward, SparseReward
from skyteam.core.actions import ChooseRerollAction, ConfirmStrategyAction, PlaceDieAction
from skyteam.core.enums import GamePhase, GameStatus, Player
from skyteam.core.game import GameConfig, SkyTeamGame
from skyteam.scenarios.loader import load_scenario

from conftest import C, P, make_game, start_placement


def yul_game(seed: int = 0, debug: bool = True) -> SkyTeamGame:
    game = SkyTeamGame(load_scenario("YUL_green"), config=GameConfig(debug=debug))
    game.reset(seed)
    return game


# ---------------------------------------------------------------- action space
def test_action_space_size_for_base_panel():
    space = ActionSpace(yul_game().panel)
    assert space.size == 583
    assert (space.discard_offset, space.use_reroll_index, space.pass_reroll_index, space.choose_offset) == (
        561, 565, 566, 567)


@pytest.mark.parametrize("player", [P, C])
def test_decode_encode_is_a_bijection(player):
    space = ActionSpace(yul_game().panel)
    for i in range(space.size):
        action = space.decode(i, player)
        assert action.player is player
        assert space.encode(action) == i


def test_same_index_means_same_thing_for_both_roles():
    space = ActionSpace(yul_game().panel)
    pilot = space.decode(1 + 2 * 140 + 5 * 7 + 4, P)
    copilot = space.decode(1 + 2 * 140 + 5 * 7 + 4, C)
    assert isinstance(pilot, PlaceDieAction) and isinstance(copilot, PlaceDieAction)
    assert (pilot.die_id, copilot.die_id) == (2, 6)
    assert pilot.slot_id == copilot.slot_id and pilot.coffee_delta == copilot.coffee_delta == 1
    assert space.decode(space.choose_offset + 0b0101, C) == ChooseRerollAction(C, (4, 6))


def test_decode_rejects_out_of_range():
    space = ActionSpace(yul_game().panel)
    with pytest.raises(ValueError):
        space.decode(space.size, P)
    with pytest.raises(ValueError):
        space.decode(-1, P)


# ---------------------------------------------------------------- action mask
def test_mask_matches_legal_actions_during_random_games():
    for seed in range(20):
        game = yul_game(seed, debug=False)
        space = ActionSpace(game.panel)
        rng = random.Random(seed)
        while not game.is_terminal():
            for player in Player:
                mask = action_mask(game, space, player)
                legal = {space.encode(a) for a in game.get_legal_actions(player)}
                assert {i for i, ok in enumerate(mask) if ok} == legal
                for i in legal:
                    assert game.is_action_legal(space.decode(i, player))
            game.step(rng.choice(game.get_legal_actions()))
        assert not any(action_mask(game, space, P)) and not any(action_mask(game, space, C))


def test_mask_is_empty_for_the_waiting_player():
    game = yul_game()
    space = ActionSpace(game.panel)
    while game.state.phase is GamePhase.STRATEGY:
        game.step(ConfirmStrategyAction(game.current_player))
    waiting = C if game.current_player is P else P
    assert not any(action_mask(game, space, waiting))


# ---------------------------------------------------------------- observation
def test_vector_size_matches_layout_and_values_in_unit_range():
    for seed in range(10):
        game = yul_game(seed, debug=False)
        rng = random.Random(seed)
        size = vector_size(game)
        assert size == sum(s.size for s in vector_layout(game))
        while True:
            for player in Player:
                v = vector_observation(game, player)
                assert len(v) == size
                assert all(0.0 <= x <= 1.0 for x in v), [(i, x) for i, x in enumerate(v) if not 0 <= x <= 1]
            if game.is_terminal():
                break
            game.step(rng.choice(game.get_legal_actions()))


def test_layout_names_are_unique():
    names = [s.name for s in vector_layout(yul_game())]
    assert len(names) == len(set(names))


def test_partner_hidden_dice_do_not_change_the_vector():
    game = make_game()
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    before = {p: vector_observation(game, p) for p in Player}
    game.debug_set_dice({d.die_id: 6 for d in game.state.dice_of(C)})
    assert vector_observation(game, P) == before[P]
    assert vector_observation(game, C) != before[C]


def test_own_dice_are_encoded_one_hot():
    game = make_game()
    start_placement(game, [1, 2, 3, 6], [1, 1, 1, 1])
    layout = vector_layout(game)
    start = sum(s.size for s in layout[:[s.name for s in layout].index("own_dice")])
    v = vector_observation(game, P)[start:start + 28]
    for ordinal, value in enumerate([1, 2, 3, 6]):
        chunk = v[ordinal * 7:(ordinal + 1) * 7]
        assert chunk == [1.0 if i == value - 1 else 0.0 for i in range(6)] + [1.0]


# ---------------------------------------------------------------- rewards
def test_sparse_reward():
    game = yul_game()
    r = SparseReward()
    action = ConfirmStrategyAction(P)
    assert r(None, action, game.state) == 0.0
    won, lost = game.state.copy(), game.state.copy()
    won.status, lost.status = GameStatus.WON, GameStatus.LOST
    assert r(None, action, won) == 1.0 and r(None, action, lost) == -1.0


def test_composite_reward_weights_terms():
    game = yul_game()
    won = game.state.copy()
    won.status = GameStatus.WON
    composite = CompositeReward((2.0, SparseReward()), (0.5, SparseReward()))
    assert composite(None, ConfirmStrategyAction(P), won) == 2.5
    assert composite.uses_before is False


# ---------------------------------------------------------------- environment
def run_episode(env: SkyTeamEnv, seed: int) -> tuple[list[float], dict]:
    rng = random.Random(seed)
    obs = env.reset(seed)
    rewards, info = [], {}
    while True:
        assert obs is not None and obs.player is env.current_player
        legal = env.legal_actions()
        assert [i for i, ok in enumerate(obs.mask) if ok] == sorted(legal)
        assert len(obs.vector) == env.observation_size
        obs, reward, terminated, truncated, info = env.step(rng.choice(legal))
        rewards.append(reward)
        if terminated or truncated:
            return rewards, info


def test_env_episode_reaches_terminal_with_sparse_reward():
    env = SkyTeamEnv(seed=0)
    assert env.action_size == 583
    for seed in range(20):
        rewards, info = run_episode(env, seed)
        assert env.done and env.game.is_terminal()
        assert all(r == 0.0 for r in rewards[:-1])
        assert rewards[-1] == (1.0 if info["status"] is GameStatus.WON else -1.0)
        assert env.legal_actions() == []
        with pytest.raises(RuntimeError):
            env.step(0)


def test_env_is_deterministic_per_seed():
    a, b = SkyTeamEnv(), SkyTeamEnv()
    assert run_episode(a, 7) == run_episode(b, 7)
    assert a.game.state.to_dict() == b.game.state.to_dict()


def test_env_truncates_at_max_steps():
    env = SkyTeamEnv(max_steps=3)
    env.reset(0)
    for _ in range(3):
        _, _, terminated, truncated, _ = env.step(env.legal_actions()[0])
    assert truncated and not terminated and env.done


def test_env_clone_is_independent():
    env = SkyTeamEnv()
    env.reset(3)
    env.step(env.legal_actions()[0])
    other = env.clone()
    snapshot = env.game.state.to_dict()
    while not other.done:
        other.step(other.legal_actions()[0])
    assert env.game.state.to_dict() == snapshot
