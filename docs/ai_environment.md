# Ambiente de IA (Etapas 10 e 11)

A engine não sabe se um jogador é humano ou agente. O módulo `skyteam/ai/` só traduz o estado e as ações
para números; as regras continuam todas em `skyteam/core` e `skyteam/mechanics`.

## Uso

```python
import random
from skyteam.ai.environment import SkyTeamEnv

env = SkyTeamEnv("YUL_green")
obs = env.reset(seed=42)              # observação do jogador que age agora
rng = random.Random(0)
while True:
    legal = env.legal_actions()        # índices legais = posições True em obs.mask
    obs, reward, terminated, truncated, info = env.step(rng.choice(legal))
    if terminated or truncated:
        break
print(info["status"], info["terminal_reason"], reward)
```

- `env.current_player` diz quem age. O jogo é por turnos, mas não alternado: a janela de rerrolagem pode
  pedir uma decisão do outro jogador. `step` devolve a observação do **próximo** jogador a agir.
- `Observation` traz `structured` (o dict da engine, só com o que o jogador pode saber), `vector` (lista de
  floats em [0, 1]) e `mask` (lista de bools do tamanho do espaço de ações).
- `max_steps` (padrão 2000) trunca episódios que não terminam.
- `env.clone()` copia o ambiente para busca (MCTS, rollouts) sem afetar o original.
- Snapshots de undo ficam desligados no ambiente (`GameConfig(keep_undo=False)`).

## Recompensa

Fica só em `skyteam/ai/rewards.py`; a engine apenas informa o resultado.

- `SparseReward`: +1 no pouso, −1 em qualquer derrota, 0 nos demais passos. Os dois jogadores recebem a
  mesma recompensa (jogo cooperativo).
- `CompositeReward((peso, fn), ...)`: soma termos para quem quiser modelar recompensas auxiliares.
  Termos com `uses_before = True` recebem uma cópia do estado anterior à ação.

## Espaço de ações (583 ações no painel base)

Fixo e relativo ao jogador: os dados são indicados pelo **ordinal** (0 a 3) entre os dados de quem age,
então o mesmo índice significa a mesma coisa para Piloto e Co-Piloto. Só depende do layout do painel.

| Índices | Ação |
|---|---|
| 0 | `ConfirmStrategy` (fim do briefing) |
| 1–560 | `PlaceDie(ordinal, espaço, café)`: `1 + ordinal·140 + espaço·7 + (café + 3)`, espaço na ordem de `data/panel/base.json`, café de −3 a +3 |
| 561–564 | `DiscardDie(ordinal)` (nunca legal no jogo base, ver P2) |
| 565 | `UseReroll` |
| 566 | `PassReroll` |
| 567–582 | `ChooseReroll(bitmask dos ordinais a relançar)` |

`ActionSpace.encode` e `ActionSpace.decode(índice, jogador)` são inversas (testado para os 583 índices).
`action_mask(game, space, player)` marca exatamente as ações de `get_legal_actions(player)`.

## Observação vetorial (181 floats no YUL)

Construída **somente** a partir da observação estruturada do jogador; os dados ocultos do parceiro não
alteram o vetor (testado). O layout vem de `vector_layout(game)` e cabe pistas de até 7 altitudes e 12
espaços de aproximação.

| Posições | Segmento | Tamanho | Conteúdo |
|---|---|---|---|
| 0–0 | `round` | 1 | round / number of altitude spaces |
| 1–6 | `phase` | 6 | one-hot GamePhase |
| 7–7 | `me_is_pilot` | 1 | 1 if the observing player is the Pilot |
| 8–8 | `me_is_current` | 1 | 1 if the observing player must act now |
| 9–9 | `me_is_active` | 1 | 1 if it is the observing player's placement turn |
| 10–11 | `pending` | 2 | one-hot kind of the first pending decision (zeros if none) |
| 12–39 | `own_dice` | 28 | per own die ordinal: one-hot value (6) + 'still hidden' flag; zeros once placed |
| 40–40 | `partner_hidden` | 1 | partner hidden dice count / dice per player |
| 41–60 | `slots_occupied` | 20 | per panel slot (panel order): 1 if occupied |
| 61–80 | `slots_value` | 20 | per panel slot: value of the piece / die sides (0 if empty) |
| 81–100 | `slots_by_pilot` | 20 | per panel slot: 1 if the piece belongs to the Pilot |
| 101–110 | `switches` | 10 | per switch slot (panel order): 1 if activated |
| 111–117 | `axis` | 7 | one-hot axis position -3..3 (clamped) |
| 118–118 | `aero_blue` | 1 | blue marker / 12 |
| 119–119 | `aero_orange` | 1 | orange marker / 12 |
| 120–123 | `brakes` | 4 | one-hot number of brakes deployed |
| 124–127 | `coffee` | 4 | one-hot coffee tokens |
| 128–128 | `reroll_supply` | 1 | reroll tokens in supply / reroll tokens in the game |
| 129–135 | `altitude` | 7 | one-hot altitude index |
| 136–142 | `altitude_rerolls` | 7 | per altitude space: reroll token still there |
| 143–149 | `first_player_pilot` | 7 | per altitude space: 1 if the Pilot starts that round |
| 150–161 | `approach` | 12 | one-hot approach position |
| 162–162 | `distance_to_airport` | 1 | remaining spaces / max approach spaces |
| 163–174 | `traffic_ahead` | 12 | airplanes on position+k (k=0..), / 4, zeros past the airport |
| 175–175 | `traffic_total` | 1 | airplanes on the track / plane tokens |
| 176–176 | `last_speed` | 1 | last speed this round / 18 (0 if not resolved) |
| 177–177 | `final_round` | 1 | 1 during the landing round |
| 178–180 | `status` | 3 | one-hot GameStatus |

## Replay

Um jogo é definido por `(cenário, seed, ações)`.

```python
from skyteam.replay import GameReplay
GameReplay.from_game(game).save("partida.json")
game2 = GameReplay.load("partida.json").run()   # erro se o resultado não se repetir
```

## Simulador headless (Etapa 11)

```bash
python -m skyteam.simulate --scenario YUL_green --games 10000 --seed 0
python -m skyteam.simulate --games 100 --json
```

O jogo `i` usa a seed `seed + i`, então qualquer partida pode ser reproduzida sozinha. Não importa nada da
interface. `benchmark_simulations(games=10000)` faz o mesmo em código.

Referência (política aleatória, 10.000 jogos de YUL, seed 0, container de desenvolvimento): cerca de
600 jogos/s e 8.500 passos/s. Resultado: 86,7% de derrota por espaço obrigatório vazio, 12,7% por giro do
eixo, 0,7% por colisão e nenhuma vitória, o esperado para jogadas aleatórias.
