"""Deterministic random number generation.

The engine never touches the global ``random`` module. Each game owns named streams
(e.g. ``dice`` for the players' dice, ``traffic`` for the Traffic die), all derived from
the game seed. Each stream's state is a single 64-bit integer, so it serialises trivially
and is stable across Python versions.

Algorithm: SplitMix64 (Steele, Lea & Flood, 2014).
"""

from __future__ import annotations

_MASK64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15


def _mix(z: int) -> int:
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
    return z ^ (z >> 31)


def next_u64(state: int) -> tuple[int, int]:
    """Return ``(new_state, value)``."""
    state = (state + _GOLDEN) & _MASK64
    return state, _mix(state)


def stream_seed(seed: int, name: str) -> int:
    """Derive an independent stream state from the game seed and a stream name."""
    h = seed & _MASK64
    for byte in name.encode("utf-8"):
        h = _mix((h ^ byte) & _MASK64)
    return h


def roll_die(state: int, sides: int = 6) -> tuple[int, int]:
    """Roll one die with an unbiased rejection sampler. Returns ``(new_state, value)``."""
    limit = _MASK64 - (_MASK64 % sides)
    while True:
        state, value = next_u64(state)
        if value < limit:
            return state, value % sides + 1


class RngStreams:
    """Mutable view over the RNG stream states stored inside ``GameState.rng``."""

    def __init__(self, states: dict[str, int]):
        self._states = states

    @staticmethod
    def initial(seed: int, names: tuple[str, ...]) -> dict[str, int]:
        return {name: stream_seed(seed, name) for name in names}

    def roll(self, stream: str, sides: int = 6) -> int:
        self._states[stream], value = roll_die(self._states[stream], sides)
        return value
