# Arquitetura (Etapa 2)

Este documento descreve a arquitetura como ela está implementada. A proposta original e o raciocínio estão em
[`00_analise_tecnica.md`](00_analise_tecnica.md).

## Camadas

```
skyteam/data/        JSON: painel, trilhas de altitude, pistas de aproximação, cenários
skyteam/scenarios/   modelo imutável (Scenario, ApproachTrack, AltitudeTrack) e carregador com validação
skyteam/core/        estado, ações, legalidade, fases, RNG, eventos, hooks, visibilidade, invariantes
skyteam/mechanics/   uma função por regra do painel (eixo, motores, rádio...) + pouso e derrotas
skyteam/modules/     Etapa 7: plugins que registram hooks
skyteam/abilities/   Etapa 8
skyteam/ai/          Etapa 10
```

Cada camada só importa as camadas de cima desta lista. O core não depende de Pygame, nem de nenhuma
biblioteca fora da stdlib.

## Peças principais

| Peça | Arquivo | Papel |
|---|---|---|
| `GameState` | `core/state.py` | Dado puro e serializável: dados, ocupação dos espaços, interruptores, marcadores, trilhas, RNG, resultado. `copy()`, `to_dict()`, `from_dict()`. |
| `PanelLayout` / `SlotDef` | `core/panel.py`, `data/panel/base.json` | Espaços do painel com dono, valores aceitos, ordem (`requires`) e obrigatoriedade. As mecânicas nunca escrevem ids ou valores fixos no código. |
| `Scenario` | `scenarios/model.py` | Configuração imutável da partida. O estado guarda só o id e os índices. |
| `Action` | `core/actions.py` | Objetos imutáveis com `player`. Serializáveis para replay. |
| `rules` | `core/rules.py` | **Única** implementação de legalidade: `violations(ctx, action)` devolve frases. `legal_actions`, `is_action_legal` e `explain_illegal_action` usam essa função. |
| `RuleContext` | `core/context.py` | O que uma mecânica, módulo ou habilidade recebe: estado, painel, cenário, RNG, `emit`, `lose`, `win` e hooks. |
| `HookRegistry` | `core/context.py` | Pontos de extensão nomeados (velocidade, antes de cada passo, fim de rodada, checagens de pouso...). |
| `GameEvent` | `core/events.py` | Histórico estruturado. Eventos com `private_to` só aparecem para aquele jogador. |
| `SkyTeamGame` | `core/game.py` | Orquestrador: decide **quando** cada regra roda. Não contém regras. |

## Fluxo de uma rodada

```
_start_round      rodada += 1, primeiro jogador = seta do espaço de altitude (R-TURN-02),
                  coleta ficha de rerrolagem (R-RER-01), hooks ROUND_START
STRATEGY          ConfirmStrategyAction do primeiro jogador e depois do parceiro
_roll_dice        stream "dice" do RNG; valores enviados como eventos privados
DICE_PLACEMENT    vez do jogador ativo; antes de cada vez, a janela de rerrolagem para o parceiro (P3)
  PlaceDieAction  valida → aplica café → ocupa o espaço → SLOT_RESOLVERS[tipo](ctx, slot, valor)
                  eixo/motores resolvem quando o 2º dado entra; motores avançam passo a passo
  UseReroll       pendência REROLL_CHOICE para cada jogador com dados escondidos
_end_round        obrigatórios (R-MAND-02) → se rodada final: checagens de fim + pouso
                  senão: desce a altitude → recolhe dados → "chegou a tempo?" → hooks de fim → nova rodada
```

As derrotas imediatas (eixo, colisão, ultrapassagem) são disparadas pela própria mecânica com `ctx.lose`.
Depois disso, nenhuma ação é legal.

## Decisões pendentes (`PendingDecision`)

Interrupções que mudam temporariamente quem decide: `REROLL_WINDOW` e `REROLL_CHOICE`. `current_player` é
sempre o jogador da primeira pendência. Fora delas, é o jogador ativo da fase. Habilidades e módulos que
pedirem escolhas usarão o mesmo mecanismo.

## Determinismo

- RNG SplitMix64 em Python puro, com streams nomeados (`dice`, `traffic`) derivados da seed. O estado de cada
  stream é um inteiro dentro do `GameState`.
- Os streams são separados para que o dado de Tráfego não desloque a sequência dos dados dos jogadores.
- Teste de regressão fixa a sequência da seed 12345. Mudar o algoritmo quebraria replays gravados.
- `(cenário, seed, ações)` reproduz estado e eventos idênticos (teste `test_same_seed_and_actions_reproduce_the_game`).

## Clone, snapshots e undo

- `clone()` copia o `GameState` (cópia explícita, sem `deepcopy`) e compartilha a configuração imutável.
- `save_state()` / `load_state()` usam `to_dict()` / `from_dict()`. O resultado é JSON puro, com os inteiros de
  64 bits do RNG como string.
- `undo_action()` restaura snapshots guardados a cada `step`. Escolhi snapshot em vez de ação inversa porque o
  estado é pequeno, e escrever o inverso de cada efeito (inclusive de módulos) seria frágil. Para simulação em
  massa, `GameConfig(keep_undo=False)` desliga os snapshots.

## Informação oculta

A única informação oculta do jogo base são os dados atrás da tela. `get_observation(player)` mostra os
próprios dados escondidos e apenas a **quantidade** de dados escondidos do parceiro. Seed e RNG nunca aparecem.
`history(player)` filtra eventos privados. Um teste confirma que alterar os dados escondidos do parceiro não
muda a observação.

## Modo debug e invariantes

- `GameConfig(debug=True)` habilita `debug_set_dice` e valida as invariantes depois de cada ação.
- `GameConfig(strict=True)` só valida.
- `validate_state()` cobre: peça em dois espaços, coerência dado↔espaço, faixas de café, eixo, freios, altitude
  e posição, conservação dos 12 tokens de Avião, ordem dos interruptores, marcadores coerentes com os
  interruptores, e status coerente com a fase.

## Como os módulos vão entrar (Etapa 7)

Um módulo registra funções nos pontos de `Hook` e guarda o próprio estado em `state.modules[id]`. Exemplos:

| Módulo | Hooks |
|---|---|
| Vento | `AFTER_AXIS` (gira a ficha), `SPEED_MODIFIER` (soma o vento) |
| Curvas | `BEFORE_PLANE_STEP` (verifica o eixo permitido) |
| Dado de Tráfego | `ROUND_START` (rola o stream `traffic`) |
| Querosene | espaço extra no painel (`SlotKind.MODULE`), `ROUND_END_FINAL_STEP` (−6) |
| Estagiário / Freios de Gelo | espaços extras, `PLACEMENT_RULES`, `GAME_END_CHECKS` |

Hoje, um cenário com módulos levanta `NotImplementedError` ao criar o jogo, para nada rodar com regras faltando.

## Resultado observado no jogo base

Com o painel base, a pendência P2 (jogador sem colocação legal) **não pode acontecer**:
- **Piloto:** ele tem Eixo, Motores, Rádio e um espaço de trem que aceita cada valor. Antes do 4º dado, usou
  só 3 espaços, e o Copiloto não ocupa nenhum espaço exclusivo do Piloto.
- **Copiloto:** ele tem Eixo, Motores e 2 Rádios sem restrição de valor, e antes do 4º dado usou no máximo 3.

`DiscardDieAction` fica para os módulos que mudam o painel, e os testes com partidas aleatórias nunca a geraram.
