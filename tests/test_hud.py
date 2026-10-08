"""Temporary Pygame HUD: draws every state and plays through clicks without crashing."""

from __future__ import annotations

import os
import random

import pytest

pygame = pytest.importorskip("pygame")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from skyteam.ui.hud import H, W, Hud  # noqa: E402


@pytest.fixture(scope="module")
def screen():
    pygame.init()
    yield pygame.display.set_mode((W, H))
    pygame.quit()


def click_center(hud: Hud, rect) -> None:
    hud.click(rect.center)


def test_full_games_by_clicking(screen):
    for seed in range(5):
        rng = random.Random(seed)
        hud = Hud(screen, seed=seed)
        for _ in range(500):
            hud.draw()
            if hud.game.is_terminal():
                break
            targets = [b.rect for b in hud.buttons if b.enabled and b.label not in ("−", "+")]
            targets += list(hud.die_rects.values())
            if hud.ui.selected_die is not None:
                targets += [hud.slot_rects[s] for s in hud.legal_slots()[0]]
            click_center(hud, rng.choice(targets))
        assert hud.game.is_terminal()
        hud.draw()


def test_cover_hides_the_dice_when_the_turn_passes(screen):
    hud = Hud(screen, seed=3)
    while hud.game.state.phase.value == "strategy":
        hud.draw()
        click_center(hud, hud.buttons[0].rect)
    hud.ui.cover_for = hud.game.current_player
    hud.draw()
    assert hud.die_rects == {} and hud.slot_rects == {}
    assert [b.label for b in hud.buttons] == ["Mostrar meus dados"]
