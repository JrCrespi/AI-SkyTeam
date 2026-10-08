"""Hidden information: a player never sees the partner's dice behind the screen."""

import pytest

from conftest import C, P, place, start_placement


@pytest.mark.rule("R-GEN-03")
def test_partner_hidden_dice_do_not_change_observation(game):
    start_placement(game, [1, 2, 3, 4], [1, 2, 3, 4])
    obs = game.get_observation(P)
    game.debug_set_dice({d.die_id: 6 for d in game.state.hidden_dice(C)})
    assert game.get_observation(P) == obs
    assert game.get_observation(C) != obs


def test_observation_exposes_own_dice_and_placed_dice(game):
    start_placement(game, [1, 2, 3, 4], [5, 5, 5, 5])
    place(game, P, "concentration.1", 1)
    obs = game.get_observation(C)
    assert obs["partner_hidden_dice_count"] == 3
    assert {d["value"] for d in obs["own_hidden_dice"]} == {5}
    assert obs["placed_dice"][0]["value"] == 1
    assert "seed" not in obs and "rng" not in obs


def test_private_events_are_filtered_from_history(game):
    start_placement(game, [1, 2, 3, 4], [5, 5, 5, 5])
    pilot_log = "\n".join(game.history(P))
    assert "copilot rolled" not in pilot_log
    assert "pilot rolled" in pilot_log
