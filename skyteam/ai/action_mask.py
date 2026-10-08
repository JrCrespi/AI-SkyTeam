"""Legal-action mask over the fixed ``ActionSpace``."""

from __future__ import annotations

from skyteam.core.enums import Player
from skyteam.core.game import SkyTeamGame

from .action_space import ActionSpace


def action_mask(game: SkyTeamGame, space: ActionSpace, player: Player) -> list[bool]:
    """``mask[i]`` is True iff ``space.decode(i, player)`` is legal now."""
    mask = [False] * space.size
    for action in game.get_legal_actions(player):
        mask[space.encode(action)] = True
    return mask
