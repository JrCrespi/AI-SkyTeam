from collections import Counter

from skyteam.core.rng import RngStreams, roll_die, stream_seed


def test_same_seed_same_sequence():
    a = RngStreams(RngStreams.initial(42, ("dice",)))
    b = RngStreams(RngStreams.initial(42, ("dice",)))
    assert [a.roll("dice") for _ in range(100)] == [b.roll("dice") for _ in range(100)]


def test_streams_are_independent():
    states = RngStreams.initial(42, ("dice", "traffic"))
    assert states["dice"] != states["traffic"]
    rng = RngStreams(states)
    before = rng.roll("dice")
    states2 = RngStreams.initial(42, ("dice", "traffic"))
    rng2 = RngStreams(states2)
    rng2.roll("traffic")
    assert rng2.roll("dice") == before


def test_known_values_are_stable_across_versions():
    # Regression guard: changing the algorithm would break every recorded replay.
    rng = RngStreams(RngStreams.initial(12345, ("dice",)))
    assert [rng.roll("dice") for _ in range(10)] == KNOWN_SEQUENCE


def test_die_distribution_is_roughly_uniform():
    state, counts = stream_seed(7, "dice"), Counter()
    for _ in range(60000):
        state, value = roll_die(state)
        counts[value] += 1
    assert set(counts) == {1, 2, 3, 4, 5, 6}
    assert all(9000 < n < 11000 for n in counts.values())


KNOWN_SEQUENCE = [4, 4, 5, 2, 3, 3, 3, 1, 1, 2]
