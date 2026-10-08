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
    assert space.size == 865
    assert (space.discard_offset, space.use_reroll_index, space.pass_reroll_index, space.choose_offset) == (
        841, 847, 848, 849)


def test_legal_actions_round_trip_through_the_index():
    """decode(encode(a)) is a legal action with the same effect: same player, value, slot and coffee."""
    for seed in range(30):
        game = yul_game(seed, debug=False)
        space = ActionSpace(game.panel)
        rng = random.Random(seed)
        while not game.is_terminal():
            for action in game.get_legal_actions():
                back = space.decode(space.encode(action, game.state), action.player, game.state)
                assert game.is_action_legal(back)
                assert type(back) is type(action) and back.player is action.player
                if isinstance(action, PlaceDieAction):
                    assert (game.state.die(back.die_id).value, back.slot_id, back.coffee_delta) == (
                        game.state.die(action.die_id).value, action.slot_id, action.coffee_delta)
                elif isinstance(action, ChooseRerollAction):
                    assert back == action
            game.step(rng.choice(game.get_legal_actions()))


def test_place_index_names_the_value_not_the_die():
    game = make_game()
    start_placement(game, [5, 2, 5, 1], [3, 3, 3, 3])
    space = ActionSpace(game.panel)
    axis = [s.id for s in game.panel.slots].index("axis.pilot")
    index = 1 + (5 - 1) * 140 + axis * 7 + 3
    fives = [d.die_id for d in game.state.dice_of(P) if d.value == 5]
    for die in fives:
        assert space.encode(PlaceDieAction(P, die, "axis.pilot"), game.state) == index
    assert space.decode(index, P, game.state) == PlaceDieAction(P, min(fives), "axis.pilot")
    with pytest.raises(ValueError):
        space.decode(1 + (4 - 1) * 140 + axis * 7 + 3, P, game.state)   # no 4 in hand


def test_reroll_mask_follows_dice_sorted_by_value():
    game = make_game()
    start_placement(game, [6, 1, 4, 2], [3, 3, 3, 3])
    space = ActionSpace(game.panel)
    by_value = {d.value: d.die_id for d in game.state.dice_of(P)}
    action = space.decode(space.choose_offset + 0b0101, P, game.state)   # 1st and 3rd smallest: 1 and 4
    assert action == ChooseRerollAction(P, tuple(sorted((by_value[1], by_value[4]))))


def test_decode_rejects_out_of_range():
    game = yul_game()
    space = ActionSpace(game.panel)
    with pytest.raises(ValueError):
        space.decode(space.size, P, game.state)
    with pytest.raises(ValueError):
        space.decode(-1, P, game.state)


# ---------------------------------------------------------------- action mask
def test_mask_matches_legal_actions_during_random_games():
    for seed in range(20):
        game = yul_game(seed, debug=False)
        space = ActionSpace(game.panel)
        rng = random.Random(seed)
        while not game.is_terminal():
            for player in Player:
                mask = action_mask(game, space, player)
                legal = {space.encode(a, game.state) for a in game.get_legal_actions(player)}
                assert {i for i, ok in enumerate(mask) if ok} == legal
                for i in legal:
                    assert game.is_action_legal(space.decode(i, player, game.state))
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


def test_own_dice_are_encoded_one_hot_sorted_by_value():
    game = make_game()
    start_placement(game, [6, 2, 3, 1], [1, 1, 1, 1])
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
    assert env.action_size == 865
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


def test_lookahead_features_match_what_the_engine_does():
    """axis_spin_if / advance_if / crash_if / too_fast_if predict the real outcome of the placement."""
    checked = 0
    for seed in range(40):
        game = yul_game(seed, debug=False)
        rng = random.Random(seed)
        layout = vector_layout(game)
        names = [s.name for s in layout]
        starts = {s.name: sum(x.size for x in layout[:names.index(s.name)]) for s in layout}
        while not game.is_terminal():
            player = game.current_player
            v = vector_observation(game, player)
            seg = lambda name: v[starts[name]:starts[name] + 6]  # noqa: E731
            for action in game.get_legal_actions(player):
                if not isinstance(action, PlaceDieAction) or action.slot_id.split(".")[0] not in ("axis", "engines"):
                    continue
                value = game.state.die(action.die_id).value + action.coffee_delta
                trial = game.clone()
                before = trial.state.approach_position
                trial.step(action)
                reason = trial.get_result()[1]
                if action.slot_id.startswith("axis") and any(seg("axis_spin_if")):
                    assert seg("axis_spin_if")[value - 1] == (1.0 if reason == "axis_spin" else 0.0)
                    checked += 1
                if action.slot_id.startswith("engines") and trial.state.last_speed is not None \
                        and game.state.slots.get(action.slot_id) is None and (any(seg("advance_if")) or any(seg("crash_if"))):
                    crashed = reason in ("collision", "overshoot")
                    assert seg("crash_if")[value - 1] == (1.0 if crashed else 0.0)
                    if not crashed:
                        assert seg("advance_if")[value - 1] * 2 == trial.state.approach_position - before
                    checked += 1
            game.step(rng.choice(game.get_legal_actions()))
    assert checked > 50


def test_landing_conditions_reward_counts_met_conditions():
    from skyteam.ai.rewards import LandingConditionsReward, TrafficClearedReward

    state = yul_game().state.copy()
    r = LandingConditionsReward()
    assert r(None, None, state) == 0.0                       # game not over
    state.status, state.terminal_reason = GameStatus.LOST, "landing_axis"
    state.traffic = [0] * len(state.traffic)
    state.axis, state.landing_speed_ok = 1, True
    for k in state.switches:
        state.switches[k] = True
    assert r(None, None, state) == 3.0                       # traffic, configuration, speed
    state.terminal_reason = "collision"
    assert r(None, None, state) == 0.0
    before = yul_game().state
    after = before.copy()
    after.traffic[3] -= 1
    assert TrafficClearedReward()(before, None, after) == 1.0
