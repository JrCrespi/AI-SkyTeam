"""Temporary Pygame HUD to try the game visually: ``python -m skyteam.ui.hud``.

Two players on one computer (hot-seat). Everything drawn here is our own simple design; it is a
test bench for the engine, not the final interface (Etapa 12). The board is drawn only from the
viewing player's observation, so the partner's hidden dice never reach the screen.

Mouse: click one of your dice, then a highlighted space. Green = legal as is, yellow = legal with
coffee (use the - / + buttons to pick the coffee change). Keys: N new game, Esc quit.
"""

from __future__ import annotations

import argparse
import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import pygame

from skyteam.core.actions import (
    Action,
    ChooseRerollAction,
    ConfirmStrategyAction,
    DiscardDieAction,
    PassRerollAction,
    PlaceDieAction,
    UseRerollAction,
)
from skyteam.core.enums import DecisionKind, GamePhase, GameStatus, Player
from skyteam.core.game import SkyTeamGame
from skyteam.scenarios.loader import load_scenario

W, H = 1280, 820

BG = (24, 30, 40)
PANEL = (38, 46, 60)
PANEL_EDGE = (70, 82, 104)
TEXT = (226, 232, 240)
MUTED = (140, 152, 170)
BLUE = (66, 133, 244)
ORANGE = (245, 148, 50)
SHARED = (150, 110, 200)
GREEN = (60, 190, 110)
YELLOW = (235, 200, 60)
RED = (220, 70, 70)
WHITE = (245, 245, 245)
SLOT_EMPTY = (54, 64, 82)

PLAYER_COLOR = {Player.PILOT: BLUE, Player.COPILOT: ORANGE}
ROLE = {Player.PILOT: "Piloto", Player.COPILOT: "Co-Piloto"}
LOSS_TEXT = {
    "axis_spin": "O avião girou (eixo chegou ao X)",
    "collision": "Colisão com outro avião",
    "overshoot": "Passou do aeroporto",
    "mandatory_slot_empty": "Espaço obrigatório vazio no fim da rodada",
    "crash_before_airport": "Chegou ao chão antes do aeroporto",
    "landing_traffic": "Pouso com avião no aeroporto",
    "landing_configuration": "Pouso sem trem de pouso ou flaps completos",
    "landing_axis": "Pouso com o avião inclinado",
    "landing_speed": "Pouso rápido demais para os freios",
}

SLOT_W, SLOT_H = 58, 58

# Our own panel layout: pilot side on the left, co-pilot side on the right, shared in the middle.
SLOT_POS: dict[str, tuple[int, int]] = {
    "radio.pilot": (50, 215),
    "gear.1": (50, 330), "gear.2": (118, 330), "gear.3": (186, 330),
    "brakes.1": (50, 470), "brakes.2": (118, 470), "brakes.3": (186, 470),
    "axis.pilot": (345, 300), "axis.copilot": (525, 300),
    "engines.pilot": (345, 400), "engines.copilot": (525, 400),
    "concentration.1": (370, 535), "concentration.2": (440, 535), "concentration.3": (510, 535),
    "radio.copilot.1": (700, 215), "radio.copilot.2": (768, 215),
    "flaps.1": (632, 330), "flaps.2": (700, 330), "flaps.3": (768, 330), "flaps.4": (836, 330),
}
GROUP_LABELS = [
    ("Rádio", 50, 192), ("Trem de pouso", 50, 307), ("Freios", 50, 447),
    ("Eixo", 345, 192), ("Motores", 345, 380), ("Concentração", 370, 512),
    ("Rádio", 700, 192), ("Flaps", 632, 307),
]


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: Callable[[], None]
    color: tuple[int, int, int] = PANEL_EDGE
    enabled: bool = True


@dataclass
class HudState:
    selected_die: int | None = None
    delta: int = 0
    reroll_pick: set[int] = field(default_factory=set)
    cover_for: Player | None = None
    last_player: Player | None = None
    message: str = ""


class Hud:
    def __init__(self, screen: pygame.Surface, scenario: str = "YUL_green", seed: int | None = None,
                 hot_seat: bool = True) -> None:
        self.screen = screen
        self.scenario = load_scenario(scenario)
        self.hot_seat = hot_seat
        self.font = pygame.font.Font(None, 22)
        self.small = pygame.font.Font(None, 18)
        self.big = pygame.font.Font(None, 34)
        self.huge = pygame.font.Font(None, 56)
        self.new_game(seed)

    # ------------------------------------------------------------------ game control
    def new_game(self, seed: int | None = None) -> None:
        self.seed = random.randrange(10**9) if seed is None else seed
        self.game = SkyTeamGame(self.scenario)
        self.game.reset(self.seed)
        self.ui = HudState()
        self._update_cover()

    @property
    def viewer(self) -> Player:
        """Whose eyes the screen shows: the player who must act (or the last one at the end)."""
        return self.game.current_player or self.ui.last_player or Player.PILOT

    def _update_cover(self) -> None:
        player = self.game.current_player
        private = self.game.state.phase is GamePhase.DICE_PLACEMENT
        if self.hot_seat and player is not None and private and player is not self.ui.last_player \
                and self.ui.last_player is not None:
            self.ui.cover_for = player
        if player is not None:
            self.ui.last_player = player

    def apply(self, action: Action) -> None:
        problems = self.game.explain_illegal_action(action)
        if problems:
            self.ui.message = problems[0]
            return
        self.game.step(action)
        self.ui.selected_die, self.ui.delta, self.ui.message = None, 0, ""
        self.ui.reroll_pick.clear()
        self._update_cover()

    # ------------------------------------------------------------------ input
    def click(self, pos: tuple[int, int]) -> None:
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(pos):
                button.action()
                return
        if self.ui.cover_for or self.game.is_terminal():
            return
        for die_id, rect in self.die_rects.items():
            if rect.collidepoint(pos):
                self._click_die(die_id)
                return
        for slot_id, rect in self.slot_rects.items():
            if rect.collidepoint(pos) and self.ui.selected_die is not None:
                self.apply(PlaceDieAction(self.viewer, self.ui.selected_die, slot_id, self.ui.delta))
                return

    def _click_die(self, die_id: int) -> None:
        pending = self.game.state.pending
        if pending and pending[0].kind is DecisionKind.REROLL_CHOICE:
            self.ui.reroll_pick ^= {die_id}
        elif self.game.state.phase is GamePhase.DICE_PLACEMENT and self.game.state.die(die_id).value:
            self.ui.selected_die = None if self.ui.selected_die == die_id else die_id
            self.ui.delta = 0

    def _set_delta(self, step: int) -> None:
        self.ui.delta += step

    # ------------------------------------------------------------------ drawing helpers
    def text(self, s: str, pos: tuple[int, int], color=TEXT, font=None, center=False) -> pygame.Rect:
        surf = (font or self.font).render(s, True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)
        return rect

    def box(self, rect, color, radius=8, width=0) -> None:
        pygame.draw.rect(self.screen, color, rect, width, border_radius=radius)

    def die_face(self, rect: pygame.Rect, value: int | None, color, selected=False) -> None:
        self.box(rect, WHITE if value else (90, 100, 120), 8)
        self.box(rect, color, 8, 3)
        if selected:
            self.box(rect.inflate(8, 8), YELLOW, 10, 3)
        if not value:
            return
        cx, cy, d = rect.centerx, rect.centery, rect.w // 4
        pips = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
                4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
                6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
        for dx, dy in pips.get(value, []):
            pygame.draw.circle(self.screen, (30, 30, 30), (cx + dx * d, cy + dy * d), max(3, rect.w // 11))

    def button(self, rect, label, action, color=PANEL_EDGE, enabled=True) -> None:
        rect = pygame.Rect(rect)
        self.buttons.append(Button(rect, label, action, color, enabled))
        self.box(rect, color if enabled else (60, 66, 78), 8)
        self.text(label, rect.center, TEXT if enabled else MUTED, center=True)

    # ------------------------------------------------------------------ frame
    def draw(self) -> None:
        self.buttons: list[Button] = []
        self.die_rects: dict[int, pygame.Rect] = {}
        self.slot_rects: dict[str, pygame.Rect] = {}
        self.screen.fill(BG)
        if self.ui.cover_for:
            self.draw_cover()
            return
        obs = self.game.get_observation(self.viewer)
        self.draw_header(obs)
        self.draw_approach(obs)
        self.draw_altitude(obs)
        self.draw_panel(obs)
        self.draw_hand(obs)
        self.draw_log()
        if self.game.is_terminal():
            self.draw_end()

    def draw_cover(self) -> None:
        p = self.ui.cover_for
        self.text(f"Vez do {ROLE[p]}", (W // 2, H // 2 - 60), PLAYER_COLOR[p], self.huge, center=True)
        self.text(f"{ROLE[p.partner]}, não olhe a tela.", (W // 2, H // 2), MUTED, self.big, center=True)

        def reveal() -> None:
            self.ui.cover_for = None
        self.button((W // 2 - 110, H // 2 + 50, 220, 50), "Mostrar meus dados", reveal, PLAYER_COLOR[p])

    def draw_header(self, obs) -> None:
        sc = self.scenario
        self.box((0, 0, W, 54), PANEL, 0)
        self.text(f"{sc.airport_name} ({sc.airport_code})", (20, 16), TEXT, self.big)
        alt = sc.altitude_track.spaces[obs["altitude_index"]]
        self.text(f"Rodada {obs['round']}/{len(sc.altitude_track.spaces)}"
                  f"   Altitude {'POUSO' if alt.final else alt.altitude}", (360, 20))
        player = self.game.current_player
        if player:
            self.text(f"Vez: {ROLE[player]}", (640, 20), PLAYER_COLOR[player], self.big)
        self.text(self.phase_hint(), (820, 22), MUTED, self.small)

    def phase_hint(self) -> str:
        s = self.game.state
        if self.game.is_terminal():
            return "Fim de jogo"
        if s.phase is GamePhase.STRATEGY:
            return "Estratégia: conversem e confirmem para lançar os dados"
        if s.pending and s.pending[0].kind is DecisionKind.REROLL_WINDOW:
            return "Usar uma ficha de rerrolagem antes da jogada?"
        if s.pending and s.pending[0].kind is DecisionKind.REROLL_CHOICE:
            return "Clique nos dados a relançar e confirme"
        return "Escolha um dado e um espaço (sem conversar sobre os dados)"

    def draw_approach(self, obs) -> None:
        traffic, pos = obs["traffic"], obs["approach_position"]
        airport = self.scenario.approach_track.airport_index
        x0, y0, w = 20, 70, 880
        self.box((x0, y0, w, 100), PANEL)
        self.text("Aproximação", (x0 + 10, y0 + 6), MUTED, self.small)
        n = len(traffic)
        cell = (w - 20) // n
        for i, t in enumerate(traffic):
            r = pygame.Rect(x0 + 10 + i * cell, y0 + 24, cell - 8, 68)
            self.box(r, (70, 60, 40) if i == airport else SLOT_EMPTY, 6)
            if i == airport:
                self.text(self.scenario.airport_code, (r.centerx, r.y + 12), YELLOW, self.font, center=True)
            for k in range(t):
                cx = r.x + 16 + (k % 4) * 22
                cy = r.y + (40 if i == airport else 22) + (k // 4) * 20
                pygame.draw.polygon(self.screen, RED, [(cx, cy - 8), (cx - 7, cy + 6), (cx + 7, cy + 6)])
            if i == pos:
                self.box(r, GREEN, 6, 3)
                pygame.draw.polygon(self.screen, WHITE, [(r.centerx, r.bottom - 22), (r.centerx - 10, r.bottom - 6),
                                                         (r.centerx + 10, r.bottom - 6)])
        self.text(f"faltam {airport - pos}", (x0 + w - 80, y0 + 6), MUTED, self.small)

    def draw_altitude(self, obs) -> None:
        x0, y0 = 920, 70
        spaces = self.scenario.altitude_track.spaces
        self.box((x0, y0, 340, 30 + 30 * len(spaces)), PANEL)
        self.text("Altitude", (x0 + 10, y0 + 6), MUTED, self.small)
        for i, sp in enumerate(spaces):
            r = pygame.Rect(x0 + 10, y0 + 24 + i * 30, 320, 26)
            current = i == obs["altitude_index"]
            self.box(r, (60, 90, 70) if current else SLOT_EMPTY, 5)
            self.text("POUSO" if sp.final else str(sp.altitude), (r.x + 10, r.y + 5))
            self.text(f"começa: {ROLE[sp.first_player]}", (r.x + 110, r.y + 5), PLAYER_COLOR[sp.first_player])
            if i < len(obs["altitude_rerolls"]) and obs["altitude_rerolls"][i]:
                pygame.draw.circle(self.screen, GREEN, (r.right - 20, r.centery), 8)
                self.text("R", (r.right - 20, r.centery), BG, self.small, center=True)

    def draw_panel(self, obs) -> None:
        c = self.game.panel.constants
        self.box((20, 180, 885, 425), PANEL)
        self.box((20, 180, 885, 425), PANEL_EDGE, 8, 2)
        for label, x, y in GROUP_LABELS:
            self.text(label, (x, y), MUTED, self.small)

        legal_now, legal_coffee = self.legal_slots()
        placed = {d["slot"]: d for d in obs["placed_dice"]}
        for s in self.game.panel.slots:
            if s.id not in SLOT_POS:
                continue
            r = pygame.Rect(*SLOT_POS[s.id], SLOT_W, SLOT_H)
            self.slot_rects[s.id] = r
            owner = PLAYER_COLOR[next(iter(s.owners))] if len(s.owners) == 1 else SHARED
            if s.id in placed:
                d = placed[s.id]
                self.die_face(r, d["value"], PLAYER_COLOR[Player(d["owner"])])
            else:
                self.box(r, SLOT_EMPTY, 8)
                self.box(r, owner, 8, 2)
                if s.values:
                    self.text("/".join(map(str, sorted(s.values))), r.center, MUTED, self.font, center=True)
                if s.mandatory:
                    self.text("!", (r.right - 10, r.y + 4), RED, self.font)
            if s.id in legal_now:
                self.box(r.inflate(6, 6), GREEN, 10, 3)
            elif s.id in legal_coffee:
                self.box(r.inflate(6, 6), YELLOW, 10, 2)
            if s.has_switch:
                on = obs["switches"].get(s.id)
                pygame.draw.circle(self.screen, GREEN if on else (80, 80, 80), (r.centerx, r.bottom + 10), 6)

        # axis: a horizon that tilts with the axis value, plus the numbered positions
        axis = obs["axis"]
        cx, cy = 475, 250
        self.box((330, 205, 290, 88), (30, 40, 54), 8)
        ang = math.radians(max(-c.axis_spin_at, min(c.axis_spin_at, axis)) * 12)
        dx, dy = math.cos(ang) * 110, math.sin(ang) * 110
        self.screen.set_clip(pygame.Rect(330, 205, 290, 66))
        pygame.draw.line(self.screen, WHITE, (cx - dx, cy + dy), (cx + dx, cy - dy), 4)
        self.screen.set_clip(None)
        pygame.draw.circle(self.screen, YELLOW, (cx, cy), 6)
        for k in range(-c.axis_spin_at, c.axis_spin_at + 1):
            x = cx + k * 38
            color = RED if abs(k) == c.axis_spin_at else (GREEN if k == axis else MUTED)
            self.text("X" if abs(k) == c.axis_spin_at else str(k), (x, 280), color, self.small, center=True)

        # speed scale with the aerodynamics markers
        blue, orange = obs["aero_blue"], obs["aero_orange"]
        x0, y0 = 330, 470
        self.text("Velocidade: avança 0 / 1 / 2", (x0, y0 - 6), MUTED, self.small)
        for i, v in enumerate(range(2, 13)):
            r = pygame.Rect(x0 + i * 26, y0 + 8, 24, 26)
            zone = GREEN if v <= blue else (YELLOW if v <= orange else RED)
            self.box(r, zone, 4)
            self.text(str(v), r.center, BG, self.small, center=True)
        last = obs["last_speed"]
        if last:
            self.text(f"última: {last}", (x0 + 210, y0 - 6), TEXT, self.small)

        # brakes, coffee, rerolls
        limit = c.brake_thresholds[obs["brakes_deployed"]]
        self.text(f"Pouso: velocidade até {limit}", (50, 548), TEXT, self.small)
        self.text("Café", (680, 470), MUTED, self.small)
        for i in range(c.coffee_max):
            pygame.draw.circle(self.screen, (150, 100, 60) if i < obs["coffee"] else SLOT_EMPTY,
                               (693 + i * 30, 500), 11)
        self.text("Rerrolagens", (680, 525), MUTED, self.small)
        for i in range(c.reroll_tokens):
            pygame.draw.circle(self.screen, GREEN if i < obs["reroll_supply"] else SLOT_EMPTY,
                               (693 + i * 30, 555), 11)

    def legal_slots(self) -> tuple[set[str], set[str]]:
        die = self.ui.selected_die
        player = self.game.current_player
        if die is None or player is None:
            return set(), set()
        now, coffee = set(), set()
        for a in self.game.get_legal_actions(player):
            if isinstance(a, PlaceDieAction) and a.die_id == die:
                (now if a.coffee_delta == self.ui.delta else coffee).add(a.slot_id)
        return now, coffee - now

    def draw_hand(self, obs) -> None:
        player = self.viewer
        y0 = 620
        self.box((20, y0, 885, 185), PANEL)
        self.text(f"Dados do {ROLE[player]}", (35, y0 + 10), PLAYER_COLOR[player], self.font)
        own = sorted(obs["own_hidden_dice"], key=lambda d: (d["value"] or 0, d["die_id"]))
        choosing = bool(self.game.state.pending) and self.game.state.pending[0].kind is DecisionKind.REROLL_CHOICE
        for i, d in enumerate(own):
            r = pygame.Rect(35 + i * 80, y0 + 40, 64, 64)
            self.die_rects[d["die_id"]] = r
            picked = d["die_id"] in self.ui.reroll_pick if choosing else d["die_id"] == self.ui.selected_die
            self.die_face(r, d["value"], PLAYER_COLOR[player], picked)
        partner = obs["partner_hidden_dice_count"]
        self.text(f"{ROLE[player.partner]}: {partner} dados escondidos", (35, y0 + 120), MUTED, self.small)
        for i in range(partner):
            self.die_face(pygame.Rect(35 + i * 30, y0 + 140, 24, 24), None, PLAYER_COLOR[player.partner])

        if self.ui.selected_die is not None and not choosing:
            value = self.game.state.die(self.ui.selected_die).value
            self.text(f"Café: {self.ui.delta:+d}   valor: {value + self.ui.delta}", (380, y0 + 45))
            self.button((380, y0 + 75, 50, 36), "−", lambda: self._set_delta(-1))
            self.button((440, y0 + 75, 50, 36), "+", lambda: self._set_delta(+1))

        self.draw_action_buttons(y0)
        if self.ui.message:
            self.text(self.ui.message[:110], (35, y0 + 168), RED, self.small)

    def draw_action_buttons(self, y0: int) -> None:
        player = self.game.current_player
        if player is None:
            return
        legal = self.game.get_legal_actions(player)
        x, y = 600, y0 + 40
        for a in legal:
            if isinstance(a, ConfirmStrategyAction):
                self.button((x, y, 290, 44), f"Confirmar estratégia ({ROLE[player]})",
                            lambda a=a: self.apply(a), GREEN)
                y += 54
            elif isinstance(a, UseRerollAction):
                self.button((x, y, 290, 44), "Usar rerrolagem", lambda a=a: self.apply(a), GREEN)
                y += 54
            elif isinstance(a, PassRerollAction):
                self.button((x, y, 290, 44), "Seguir sem rerrolar", lambda a=a: self.apply(a))
                y += 54
            elif isinstance(a, DiscardDieAction) and a.die_id == self.ui.selected_die:
                self.button((x, y, 290, 44), "Descartar dado", lambda a=a: self.apply(a), RED)
                y += 54
        if any(isinstance(a, ChooseRerollAction) for a in legal):
            pick = tuple(sorted(self.ui.reroll_pick))
            label = f"Relançar {len(pick)} dado(s)" if pick else "Não relançar"
            self.button((x, y, 290, 44), label, lambda: self.apply(ChooseRerollAction(player, pick)), GREEN)

    def draw_log(self) -> None:
        x0, y0 = 920, 320
        self.box((x0, y0, 340, 485), PANEL)
        self.text("Histórico", (x0 + 10, y0 + 6), MUTED, self.small)
        rows: list[tuple[str, tuple[int, int, int]]] = []
        for line in self.game.history(self.viewer):
            color = TEXT if line.startswith("  ") else YELLOW
            words, cur = line.strip().split(), ""
            for w in words:
                if self.small.size(cur + " " + w)[0] > 315 and cur:
                    rows.append((cur, color))
                    cur = "   " + w
                else:
                    cur = f"{cur} {w}".strip() if not cur.startswith("   ") else f"{cur} {w}"
            rows.append((cur, color))
        for i, (row, color) in enumerate(rows[-26:]):
            self.text(row, (x0 + 10, y0 + 26 + i * 17), color, self.small)

    def draw_end(self) -> None:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        status, reason = self.game.get_result()
        won = status is GameStatus.WON
        self.text("POUSO PERFEITO!" if won else "Derrota", (W // 2, H // 2 - 60), GREEN if won else RED,
                  self.huge, center=True)
        if not won:
            self.text(LOSS_TEXT.get(str(reason), str(reason)), (W // 2, H // 2), TEXT, self.big, center=True)
        self.button((W // 2 - 100, H // 2 + 50, 200, 50), "Novo jogo", lambda: self.new_game(), GREEN)


def run(scenario: str = "YUL_green", seed: int | None = None, hot_seat: bool = True) -> None:
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Sky Team - HUD de teste")
    hud = Hud(screen, scenario, seed, hot_seat)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                hud.new_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hud.click(event.pos)
        hud.draw()
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="HUD provisório do Sky Team (2 jogadores, mesmo computador).")
    parser.add_argument("--scenario", default="YUL_green")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-hot-seat", action="store_true", help="não cobre a tela entre os turnos")
    args = parser.parse_args(argv)
    run(args.scenario, args.seed, not args.no_hot_seat)


if __name__ == "__main__":
    main()
