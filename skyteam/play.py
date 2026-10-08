"""Two players on one computer, in the terminal: ``python -m skyteam.play``.

Hot-seat: the screen is cleared and the game waits for Enter whenever the turn passes to the
other player, so neither sees the partner's hidden dice. Only the engine's public API is used.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections.abc import Callable

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
from skyteam.replay import save_finished_game
from skyteam.scenarios.loader import load_scenario

ROLE = {Player.PILOT: "Piloto (azul)", Player.COPILOT: "Co-Piloto (laranja)"}
SHORT = {Player.PILOT: "Piloto", Player.COPILOT: "Co-Piloto"}

SLOT_NAMES = {
    "axis.pilot": "Eixo (Piloto)",
    "axis.copilot": "Eixo (Co-Piloto)",
    "engines.pilot": "Motores (Piloto)",
    "engines.copilot": "Motores (Co-Piloto)",
    "radio.pilot": "Rádio (Piloto)",
    "radio.copilot.1": "Rádio 1 (Co-Piloto)",
    "radio.copilot.2": "Rádio 2 (Co-Piloto)",
    "gear.1": "Trem de pouso [1-2]",
    "gear.2": "Trem de pouso [3-4]",
    "gear.3": "Trem de pouso [5-6]",
    "flaps.1": "Flaps 1 [1-2]",
    "flaps.2": "Flaps 2 [2-3]",
    "flaps.3": "Flaps 3 [4-5]",
    "flaps.4": "Flaps 4 [5-6]",
    "brakes.1": "Freio 1 [2]",
    "brakes.2": "Freio 2 [4]",
    "brakes.3": "Freio 3 [6]",
    "concentration.1": "Concentração 1",
    "concentration.2": "Concentração 2",
    "concentration.3": "Concentração 3",
}


def slot_name(slot_id: str) -> str:
    return SLOT_NAMES.get(slot_id, slot_id)


# ---------------------------------------------------------------- screen
def clear() -> None:
    print("\033[2J\033[H", end="")


def render(game: SkyTeamGame, player: Player) -> str:
    """Board as seen by ``player``: public information plus their own hidden dice."""
    obs = game.get_observation(player)
    sc = game.scenario
    c = game.panel.constants
    alt = sc.altitude_track.spaces[obs["altitude_index"]]
    pos = obs["approach_position"]
    airport = sc.approach_track.airport_index
    lines = [f"=== {sc.airport_name} ({sc.airport_code}) | Rodada {obs['round']} de "
             f"{len(sc.altitude_track.spaces)} ==="]
    lines.append(f"Altitude: {'POUSO (rodada final)' if alt.final else alt.altitude}   "
                 f"Começa a rodada: {ROLE[alt.first_player]}")

    track = []
    for i, t in enumerate(obs["traffic"]):
        planes = "-" if not t else ("1 avião" if t == 1 else f"{t} aviões")
        cell = f"AEROPORTO: {planes}" if i == airport else planes
        track.append(f"[{'>' if i == pos else ' '}{cell}]")
    lines.append("Aproximação (início → aeroporto, > = vocês): " + " ".join(track) + f"   (faltam {airport - pos} espaços)")

    axis = obs["axis"]
    bar = "".join("X" if abs(i) == c.axis_spin_at else ("|" if i == axis else "-")
                  for i in range(-c.axis_spin_at, c.axis_spin_at + 1))
    lines.append(f"Eixo: {bar}  ({axis:+d}; gira em ±{c.axis_spin_at})")
    blue, orange = obs["aero_blue"], obs["aero_orange"]
    lines.append(f"Velocidade: até {blue} avança 0 | {blue + 1} a {orange} avança 1 | "
                 f"{orange + 1}+ avança 2")
    limit = c.brake_thresholds[obs["brakes_deployed"]]
    lines.append(f"Freios acionados: {obs['brakes_deployed']} (no pouso, velocidade deve ser no máximo {limit})")
    lines.append(f"Café: {obs['coffee']}   Rerrolagens disponíveis: {obs['reroll_supply']}")

    switches = [slot_name(s) for s, on in obs["switches"].items() if on]
    lines.append("Acionados: " + (", ".join(switches) if switches else "nenhum"))
    placed = {d["slot"]: d for d in obs["placed_dice"]}
    if placed:
        lines.append("Dados no painel nesta rodada:")
        for s in game.panel.slots:
            if s.id in placed:
                d = placed[s.id]
                lines.append(f"   {slot_name(s.id):22s} {d['value']}  ({SHORT[Player(d['owner'])]})")
    mandatory = [slot_name(s.id) for s in game.panel.slots if s.mandatory and s.id not in placed]
    if mandatory and obs["phase"] == GamePhase.DICE_PLACEMENT.value:
        lines.append("Ainda obrigatórios: " + ", ".join(mandatory))

    lines.append("")
    own = sorted(d["value"] for d in obs["own_hidden_dice"] if d["value"] is not None)
    lines.append(f"Você é o {ROLE[player]}. Seus dados: {own if own else '(nenhum)'}   "
                 f"Dados escondidos do parceiro: {obs['partner_hidden_dice_count']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- choosing an action
Prompt = Callable[[str], str]


def describe(game: SkyTeamGame, action: Action) -> str:
    if isinstance(action, ConfirmStrategyAction):
        return "Terminar a conversa de estratégia e lançar os dados"
    if isinstance(action, PlaceDieAction):
        value = game.state.die(action.die_id).value
        if action.coffee_delta:
            return (f"{slot_name(action.slot_id)} com valor {value + action.coffee_delta} "
                    f"(gasta {abs(action.coffee_delta)} café)")
        return slot_name(action.slot_id)
    if isinstance(action, DiscardDieAction):
        return f"Descartar o dado {game.state.die(action.die_id).value} (nenhuma colocação possível)"
    if isinstance(action, UseRerollAction):
        return "Usar uma ficha de rerrolagem"
    if isinstance(action, PassRerollAction):
        return "Não usar rerrolagem agora"
    if isinstance(action, ChooseRerollAction):
        if not action.die_ids:
            return "Não relançar nenhum dado"
        return "Relançar " + ", ".join(str(game.state.die(d).value) for d in action.die_ids)
    return action.describe()


def ask_number(prompt: Prompt, text: str, count: int, game: SkyTeamGame, player: Player) -> int | None:
    """Returns 0..count-1, or None to go back. Handles the log and quit commands."""
    while True:
        answer = prompt(text).strip().lower()
        if answer in ("q", "sair"):
            raise KeyboardInterrupt
        if answer in ("h", "historico", "histórico"):
            print("\n".join(game.history(player)[-30:]))
            continue
        if answer in ("v", "voltar"):
            return None
        if answer.isdigit() and 1 <= int(answer) <= count:
            return int(answer) - 1
        print(f"Digite um número de 1 a {count} (h = histórico, v = voltar, q = sair).")


def choose_action(game: SkyTeamGame, player: Player, prompt: Prompt) -> Action:
    legal = game.get_legal_actions(player)
    placements = [a for a in legal if isinstance(a, PlaceDieAction)]
    others = [a for a in legal if not isinstance(a, PlaceDieAction)]
    if not placements:
        options = others
        for i, a in enumerate(options, 1):
            print(f"  {i}. {describe(game, a)}")
        while (n := ask_number(prompt, "> ", len(options), game, player)) is None:
            pass
        return options[n]

    while True:
        dice = sorted({a.die_id for a in placements}, key=lambda d: (game.state.die(d).value, d))
        menu: list[tuple[str, int | Action]] = [(f"Colocar o dado {game.state.die(d).value}", d) for d in dice]
        menu += [(describe(game, a), a) for a in others]
        print("Escolha um dado:")
        for i, (text, _) in enumerate(menu, 1):
            print(f"  {i}. {text}")
        n = ask_number(prompt, "> ", len(menu), game, player)
        if n is None:
            continue
        choice = menu[n][1]
        if isinstance(choice, Action):
            return choice
        options = [a for a in placements if a.die_id == choice]
        options.sort(key=lambda a: (abs(a.coffee_delta), [s.id for s in game.panel.slots].index(a.slot_id)))
        print(f"Onde colocar o dado {game.state.die(choice).value}?  (v = escolher outro dado)")
        for i, a in enumerate(options, 1):
            print(f"  {i}. {describe(game, a)}")
        m = ask_number(prompt, "> ", len(options), game, player)
        if m is not None:
            return options[m]


# ---------------------------------------------------------------- game loop
def needs_privacy(game: SkyTeamGame) -> bool:
    return game.state.phase is GamePhase.DICE_PLACEMENT


def play(scenario: str = "YUL_green", seed: int | None = None, prompt: Prompt = input,
         hot_seat: bool = True, save_dir: str | None = None) -> SkyTeamGame:
    seed = random.randrange(10**9) if seed is None else seed
    game = SkyTeamGame(load_scenario(scenario))
    game.reset(seed)
    print(f"Sky Team: {game.scenario.airport_name}. Seed {seed} (use --seed {seed} para repetir).")
    seen = {Player.PILOT: 0, Player.COPILOT: 0}
    last_player: Player | None = None
    while not game.is_terminal():
        player = game.current_player
        if hot_seat and needs_privacy(game) and player is not last_player:
            clear()
            prompt(f"Passe para o {ROLE[player]}. {ROLE[player.partner]}, não olhe. Enter para continuar.")
            clear()
        last_player = player

        new = game.history(player)
        if seen[player] and len(new) > seen[player]:
            print("Últimos acontecimentos:")
            print("\n".join(new[seen[player]:]))
            print()
        seen[player] = len(new)

        print(render(game, player))
        print()
        state = game.state
        if state.phase is GamePhase.STRATEGY:
            print("Fase de estratégia: conversem à vontade (os dados ainda não foram lançados).")
        elif state.pending and state.pending[0].kind is DecisionKind.REROLL_WINDOW:
            print("Antes da próxima jogada, vocês podem usar uma ficha de rerrolagem.")
        elif state.pending and state.pending[0].kind is DecisionKind.REROLL_CHOICE:
            print("Rerrolagem: escolha quais dos seus dados relançar.")
        else:
            print("Sua vez de colocar um dado. Lembre-se: sem conversar sobre os dados.")
        game.step(choose_action(game, player, prompt))

    print("\n".join(game.history()[-12:]))
    if save_dir:
        print(f"Partida salva em {save_finished_game(game, save_dir)}")
    status, reason = game.get_result()
    print()
    if status is GameStatus.WON:
        print("*** POUSO PERFEITO! Vocês venceram. ***")
    else:
        print(f"*** Fim de jogo: derrota ({reason}). ***")
    return game


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sky Team para 2 jogadores no mesmo computador.")
    parser.add_argument("--scenario", default="YUL_green")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-hot-seat", action="store_true", help="não esconde a tela entre os turnos")
    parser.add_argument("--games-dir", default="games", help="onde salvar as partidas terminadas")
    parser.add_argument("--no-save", action="store_true", help="não salva as partidas")
    args = parser.parse_args(argv)
    try:
        play(args.scenario, args.seed, hot_seat=not args.no_hot_seat,
             save_dir=None if args.no_save else args.games_dir)
    except (KeyboardInterrupt, EOFError):
        print("\nJogo encerrado.")
        sys.exit(0)


if __name__ == "__main__":
    main()
