import pytest

from conftest import FIXTURES
from skyteam.core.enums import Player, SlotKind
from skyteam.core.exceptions import DataError
from skyteam.core.panel import load_panel
from skyteam.scenarios.loader import load_altitude_track, parse_approach_track, parse_altitude_track, load_scenario


def test_base_panel_matches_manual():
    panel = load_panel()
    assert len(panel.slots_of(SlotKind.RADIO)) == 3                                   # R-RAD-01
    assert [s.values for s in panel.slots_of(SlotKind.LANDING_GEAR)] == [
        frozenset({1, 2}), frozenset({3, 4}), frozenset({5, 6})]                      # R-GEA-01
    assert [s.values for s in panel.slots_of(SlotKind.FLAPS)] == [
        frozenset({1, 2}), frozenset({2, 3}), frozenset({4, 5}), frozenset({5, 6})]   # R-FLA-01
    assert [s.values for s in panel.slots_of(SlotKind.BRAKES)] == [
        frozenset({2}), frozenset({4}), frozenset({6})]                               # R-BRK-01
    assert len(panel.slots_of(SlotKind.CONCENTRATION)) == 3                           # R-COF-01
    assert {s.id for s in panel.mandatory_slots()} == {
        "axis.pilot", "axis.copilot", "engines.pilot", "engines.copilot"}             # R-MAND-01


@pytest.mark.rule("R-TURN-02")
def test_green_yellow_altitude_track():
    track = load_altitude_track("green_yellow")
    assert [s.altitude for s in track.spaces] == [6000, 5000, 4000, 3000, 2000, 1000, 0]
    assert [s.first_player for s in track.spaces] == [
        Player.PILOT, Player.COPILOT, Player.PILOT, Player.COPILOT, Player.PILOT, Player.COPILOT, Player.PILOT]
    assert [s.reroll for s in track.spaces] == [True, False, False, False, True, False, False]
    assert track.spaces[-1].final and track.verified


def test_approach_track_must_end_at_airport():
    with pytest.raises(DataError):
        parse_approach_track({"id": "x", "airport": "X", "spaces": [{"airport": True}, {}]})


def test_altitude_track_must_end_with_final_space():
    with pytest.raises(DataError):
        parse_altitude_track({"id": "x", "spaces": [{"altitude": 1, "first_player": "pilot", "final": True},
                                                    {"altitude": 0, "first_player": "pilot"}]})


def test_test_scenario_is_never_marked_verified():
    assert not load_scenario("TEST_basic", (FIXTURES,)).verified
