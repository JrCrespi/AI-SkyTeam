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

## Espaço de ações (865 ações no painel base)

Fixo e relativo ao jogador. Os dados são indicados pelo **valor**, não pela identidade: dois dados
escondidos com o mesmo valor são intercambiáveis, então "pôr um 5 no Eixo" é sempre o mesmo índice, em
qualquer partida e para os dois papéis. Isso é o que permite à rede aprender o significado de cada ação.
Só depende do layout do painel.

| Índices | Ação |
|---|---|
| 0 | `ConfirmStrategy` (fim do briefing) |
| 1–840 | `PlaceDie(valor, espaço, café)`: `1 + (valor−1)·140 + espaço·7 + (café + 3)`, espaço na ordem de `data/panel/base.json`, café de −3 a +3 |
| 841–846 | `DiscardDie(valor)` (nunca legal no jogo base, ver P2) |
| 847 | `UseReroll` |
| 848 | `PassReroll` |
| 849–864 | `ChooseReroll(bitmask)`: bit k = k-ésimo dado escondido em ordem crescente de valor |

`ActionSpace.encode(ação, estado)` e `ActionSpace.decode(índice, jogador, estado)`: decodificar escolhe
o dado escondido com aquele valor (o de menor id). Toda ação legal volta legal e com o mesmo efeito
(testado). `action_mask(game, space, player)` marca exatamente as ações de `get_legal_actions(player)`.

## Observação vetorial (234 floats no YUL)

Construída **somente** a partir da observação estruturada do jogador; os dados ocultos do parceiro não
alteram o vetor (testado). O layout vem de `vector_layout(game)` e cabe pistas de até 7 altitudes e 12
espaços de aproximação.

Os últimos segmentos são **derivados**: calculam, com as fórmulas da própria engine, o efeito de pôr cada
valor no meu Eixo ou nos meus Motores agora (gira? avança quanto? colide? passa da velocidade dos freios?).
Usam só o que o jogador vê. Um teste confere essas previsões contra o resultado real da jogada. Sem eles a
rede demorava muito para aprender a aritmética do eixo.

| Posições | Segmento | Tamanho | Conteúdo |
|---|---|---|---|
| 0–0 | `round` | 1 | round / number of altitude spaces |
| 1–6 | `phase` | 6 | one-hot GamePhase |
| 7–7 | `me_is_pilot` | 1 | 1 if the observing player is the Pilot |
| 8–8 | `me_is_current` | 1 | 1 if the observing player must act now |
| 9–9 | `me_is_active` | 1 | 1 if it is the observing player's placement turn |
| 10–11 | `pending` | 2 | one-hot kind of the first pending decision (zeros if none) |
| 12–39 | `own_dice` | 28 | own hidden dice sorted by value: one-hot value (6) + 'present' flag; zeros past the last |
| 40–45 | `own_value_counts` | 6 | per value 1..6: own hidden dice showing it / dice per player |
| 46–46 | `partner_hidden` | 1 | partner hidden dice count / dice per player |
| 47–66 | `slots_occupied` | 20 | per panel slot (panel order): 1 if occupied |
| 67–86 | `slots_value` | 20 | per panel slot: value of the piece / die sides (0 if empty) |
| 87–106 | `slots_by_pilot` | 20 | per panel slot: 1 if the piece belongs to the Pilot |
| 107–116 | `switches` | 10 | per switch slot (panel order): 1 if activated |
| 117–123 | `axis` | 7 | one-hot axis position -3..3 (clamped) |
| 124–124 | `aero_blue` | 1 | blue marker / 12 |
| 125–125 | `aero_orange` | 1 | orange marker / 12 |
| 126–129 | `brakes` | 4 | one-hot number of brakes deployed |
| 130–133 | `coffee` | 4 | one-hot coffee tokens |
| 134–134 | `reroll_supply` | 1 | reroll tokens in supply / reroll tokens in the game |
| 135–141 | `altitude` | 7 | one-hot altitude index |
| 142–148 | `altitude_rerolls` | 7 | per altitude space: reroll token still there |
| 149–155 | `first_player_pilot` | 7 | per altitude space: 1 if the Pilot starts that round |
| 156–167 | `approach` | 12 | one-hot approach position |
| 168–168 | `distance_to_airport` | 1 | remaining spaces / max approach spaces |
| 169–180 | `traffic_ahead` | 12 | airplanes on position+k (k=0..), / 4, zeros past the airport |
| 181–181 | `traffic_total` | 1 | airplanes on the track / plane tokens |
| 182–182 | `last_speed` | 1 | last speed this round / 18 (0 if not resolved) |
| 183–183 | `final_round` | 1 | 1 during the landing round |
| 184–186 | `status` | 3 | one-hot GameStatus |
| 187–193 | `axis_rel` | 7 | one-hot axis from my side: sign flipped for the Co-Pilot, so a partner die higher than mine always moves it up |
| 194–200 | `partner_axis_die` | 7 | one-hot value of the partner's Axis die + 'placed' flag |
| 201–207 | `partner_engine_die` | 7 | one-hot value of the partner's Engines die + 'placed' flag |
| 208–209 | `my_axis_engine_placed` | 2 | 1 if my Axis / my Engines die is already placed |
| 210–215 | `axis_spin_if` | 6 | per value v: 1 if putting v on my Axis space now spins the plane |
| 216–221 | `advance_if` | 6 | per value v: spaces advanced / 2 if v completes the Engines now |
| 222–227 | `crash_if` | 6 | per value v: 1 if v on my Engines now collides or overshoots |
| 228–233 | `too_fast_if` | 6 | per value v (landing round): 1 if v makes the speed beat the brakes |

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

## Treinamento da IA

Requer `pip install -e ".[train]"` (torch e numpy). A engine continua sem dependências.

### Autojogo (PPO)

```bash
python -m skyteam.ai.ppo --steps 12000000 --envs 128 --workers 4 --config-bonus 0.2 --out runs/meu_treino
```

Uma única rede (MLP 3×256, cabeças de política e de valor) joga pelos dois assentos; cada jogador só
recebe a própria observação, então a rede não vê os dados escondidos do parceiro. Os logits fora da
máscara são descartados. O treino roda vários jogos em paralelo (`--envs`, `--workers`) e, a cada
`--eval-every` atualizações, avalia a política gulosa em `--eval-games` jogos com seeds fixas
(a partir de 1.000.000, nunca usadas no treino). Em `--out` ficam `best.pt` (melhor avaliação),
`last.pt` e `history.json`. `--init modelo.pt` continua um treino anterior.

Recompensa de treino (`training_reward` em `rewards.py`): ±1 no fim do jogo, mais termos de
modelagem para que o sinal apareça antes da primeira vitória. São eles: rodada sobrevivida
(`--round-bonus`), progresso na pista (`--progress-bonus`), cada interruptor de trem de pouso, flaps
e freios (`--config-bonus`), cada avião do tráfego retirado (`--traffic-bonus`) e cada condição de
pouso cumprida no último turno (`--landing-bonus`). A engine não sabe nada disso.

### Aprender com partidas gravadas

Toda partida jogada no terminal (`skyteam.play`) ou no HUD é salva em `games/`. Para treinar a rede
imitando essas jogadas (as jogadas de partidas vencidas pesam mais, `--win-weight`):

```bash
python -m skyteam.ai.imitation --data games --out runs/bc.pt
python -m skyteam.ai.ppo --init runs/bc.pt --out runs/a_partir_das_partidas
```

`--init` também aceita um modelo já treinado, para refinar o modelo publicado com as suas partidas.

### Avaliar

```bash
python -m skyteam.simulate --scenario YUL_green --policy models/yul_ppo.pt --games 1000
```

### Modelo publicado

`models/yul_ppo.pt` foi treinado só por autojogo no YUL (pista verde/amarela). Em 2.000 jogos com seeds nunca vistas
no treino (`--seed 5000000`), pousa em **82%** das partidas (a política aleatória pousa em 0%). As derrotas
restantes são, em ordem: configuração de pouso incompleta (6%), eixo fora do centro no pouso (4,3%),
tráfego ainda na pista (2,5%), velocidade acima dos freios (2,2%) e espaço obrigatório vazio (1,4%).
A partida dura em média cerca de 75 decisões e o modelo joga cerca de 16 partidas por segundo em CPU.

O treino partiu do zero e foi feito em etapas, cada uma continuando a anterior com `--init`, enquanto
os termos de modelagem eram ajustados. A última etapa usou o comando de exemplo acima (12 milhões de
passos, cerca de 85 minutos em 4 núcleos de CPU) e subiu a taxa de pouso nas seeds de avaliação de 0,3%
para cerca de 80%.
