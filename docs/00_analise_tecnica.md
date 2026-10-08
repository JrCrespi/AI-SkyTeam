# Sky Team em Python: análise técnica inicial

> Documento da primeira resposta (seção 43 do pedido). Nenhum código de jogo foi escrito ainda.
> Toda regra citada aqui vem de conhecimento prévio do jogo e **não foi conferida com o manual oficial**,
> porque os manuais ainda não foram fornecidos ao projeto. Ver `docs/etapa1/` para o registro de regras
> e o status de verificação de cada uma.

---

## 1. Entendimento do objetivo

Construir uma **engine de regras** de Sky Team que seja:

- **fiel** ao manual oficial (nenhuma regra inventada; dúvidas viram `TODO_RULE_VERIFICATION`);
- **headless**: a partida inteira roda sem UI, sem Pygame, sem imagens;
- **determinística**: `(cenário, seed, lista de ações)` reproduz exatamente a mesma partida;
- **orientada a dados**: aeroportos, pistas de aproximação, esteiras de altitude e cenários são JSON;
- **extensível**: módulos e habilidades plugáveis via interfaces e hooks, sem `if scenario == ...`;
- **pronta para IA**: observação por jogador (informação imperfeita), espaço de ações fixo com máscara,
  clone/snapshot baratos para MCTS, recompensa fora da engine.

A UI (Pygame) é um cliente da engine, igual a um agente: lê estado/observação, pede ações legais, envia uma ação.

Princípio que guia todo o resto: **o `GameState` é dado puro; as regras são funções sobre esse dado.**
Isso torna serialização, clone, replay, undo e testes triviais.

---

## 2. Arquitetura sugerida

Camadas, de dentro para fora (cada uma só importa as de dentro):

```
data (JSON)  →  core (estado, ações, fluxo, RNG, eventos)  →  mechanics (regras de cada controle)
             →  modules / abilities (plugins via hooks)     →  ai (env, observação, máscara, reward)
             →  simulate / replay (CLI headless)            →  ui (Pygame, último)
```

Decisões principais:

| Decisão | Escolha | Justificativa |
|---|---|---|
| Linguagem/versão | Python 3.11+, sem dependências no core | `core`, `mechanics`, `modules`, `abilities`, `ai` só usam stdlib. Pygame só em `ui/`. |
| Estado | `@dataclass(slots=True)` mutável, só tipos primitivos/enum/listas/dicts | Serializável, copiável rápido, sem objetos gráficos. |
| Regras | Funções puras por mecânica (`mechanics/*.py`) chamadas pelo orquestrador | Regras não ficam espalhadas em `game.py`; cada mecânica é testável isolada. |
| Layout do painel | Painel de controle descrito como **slots em dados** | Módulos podem adicionar/alterar slots sem tocar no core (ex.: um módulo que cria um espaço novo). |
| RNG | PRNG próprio (PCG32 ou SplitMix64) em Python puro, estado = um inteiro | `random.Random` serializa mal e pode mudar entre versões do Python; um PRNG próprio é estável e cabe no snapshot. |
| Extensão | Dois mecanismos: **eventos** (notificação) e **hooks de regra** (interceptação/consulta) | Eventos sozinhos não bastam: uma habilidade que muda o valor permitido num slot precisa *alterar a resposta* de uma consulta, não só reagir. |
| Decisões pendentes | Pilha de `PendingDecision` no estado | Rerolls, escolhas de alvo de habilidades e qualquer interrupção viram "quem decide o quê agora", e `current_player` deriva daí. |
| Undo | Pilha de snapshots compactos (não ações inversas) | O estado é pequeno (dezenas de campos); copiar é mais barato e muito mais seguro que escrever o inverso de cada efeito. |
| Dados de cenário | JSON (stdlib) com validação própria no carregamento | Sem dependência de PyYAML; erros de dados aparecem no load, não no meio da partida. |

---

## 3. Modelo de `GameState`

Esboço (nomes finais podem mudar na Etapa 2):

```python
@dataclass(slots=True)
class DieState:
    die_id: int                 # 0..3 pilot, 4..7 copilot (ids globais estáveis)
    owner: Player
    value: int | None           # None = ainda não rolado nesta rodada
    location: str | None        # slot_id onde foi colocado; None = na mão
    placed_order: int | None    # ordem de colocação na rodada (para log/regras de ordem)

@dataclass(slots=True)
class SlotState:
    slot_id: str                # "axis.pilot", "engines.copilot", "flaps.2", "coffee.1", ...
    die_id: int | None
    activated: bool             # para switches que permanecem ativados entre rodadas

@dataclass(slots=True)
class GameState:
    # identidade
    scenario_id: str
    airport_code: str
    rng_state: int
    # fluxo
    round_index: int            # 0-based
    phase: GamePhase
    active_player: Player | None
    pending: list[PendingDecision]
    placements_this_round: int
    # tabuleiro
    altitude_index: int         # posição na esteira de altitude (dados do cenário)
    approach_index: int         # posição da aeronave na pista de aproximação
    traffic: list[int]          # nº de aviões em cada espaço da aproximação
    axis: int                   # inclinação, 0 = nivelado; sinal = lado
    aero_blue: int              # marcador aerodinâmico azul (velocidade mínima / limiar 1)
    aero_orange: int            # marcador aerodinâmico laranja (limiar 2)
    brakes_marker: int          # marcador vermelho de frenagem
    slots: dict[str, SlotState]
    dice: list[DieState]
    coffee_tokens: int
    rerolls_available: int
    # extensões
    modules: dict[str, dict]    # estado interno de cada módulo, serializável
    abilities: dict[str, AbilityState]
    effects: list[TemporaryEffect]
    # resultado
    status: GameStatus          # IN_PROGRESS / WON / LOST
    terminal_reason: str | None # LossReason/WinReason como string estável
    last_engine_sum: int | None # informação pública útil para UI/IA
```

- **Informação pública × privada** não é um campo separado: é uma *função* de visibilidade
  (`visibility.py`) aplicada sobre o estado completo. O estado completo é a verdade; observações são projeções.
- `to_dict()` / `from_dict()` gerados a partir dos dataclasses (enum → nome). Teste de ida e volta para toda fixture.
- `validate_state()` checa invariantes (seção 29): cada dado em no máximo um slot, slot ocupado ↔ dado com
  aquele `location`, marcadores dentro dos limites da esteira, café entre 0 e o máximo, tráfego ≥ 0,
  `approach_index` dentro da pista, ordem dos switches respeitada, módulos ativos ∈ cenário.

---

## 4. Modelo de `Action`

Ações são `@dataclass(frozen=True)`, todas com `player`. Conjunto inicial:

```python
PlaceDieAction(player, die_id, slot_id, coffee_delta: int = 0)
ConfirmStrategyAction(player)                   # fim da fase de estratégia/briefing
UseRerollAction(player)                         # gasta um token de reroll
ChooseRerollDiceAction(player, die_ids: tuple)  # resposta à decisão pendente de reroll
UseAbilityAction(player, ability_id, params: tuple)
ModuleAction(player, module_id, kind: str, params: tuple)  # ações específicas de módulos
```

Pontos de projeto:

- **Café é aplicado na mesma ação de colocação** (`coffee_delta`): pelo que conheço da regra, o café ajusta o
  valor do dado no momento de colocar. Fazer isso atômico evita estados intermediários inúteis e simplifica
  a máscara. `TODO_RULE_VERIFICATION` (R-COF-03).
- `game.get_legal_actions(player)` enumera; `game.is_action_legal(a)` e `game.explain_illegal_action(a)` usam
  **o mesmo validador**, que devolve uma lista de `Violation(code, message)`. Nunca há duas implementações
  da legalidade.
- **Codificação para IA** (`ai/action_space.py`): mapeamento fixo e bijetivo `Action ↔ int`.
  Para colocação: `índice_do_dado_na_mão (0..3) × slot (N_SLOTS do registro global) × delta de café`.
  Rerolls: um índice por subconjunto de dados (2⁴). Habilidades/módulos: blocos reservados por id do registro.
  O espaço é fixo para todas as partidas (cenários sem um slot simplesmente o mascaram).

---

## 5. Fluxo completo de uma rodada

Fluxo como entendo hoje (cada passo tem uma regra no registro da Etapa 1 a confirmar):

```
ROUND_START
  └─ aplica efeitos do espaço atual da esteira de altitude (ex.: ganhar reroll)       R-ALT-*
  └─ hooks on_round_start de módulos/habilidades
STRATEGY  (briefing: jogadores podem conversar, ainda sem dados)                       R-COM-*
  └─ cada jogador envia ConfirmStrategyAction
DICE_ROLL
  └─ cada jogador rola seus 4 dados atrás do escudo (RNG da partida)                   R-DIE-*
PLACEMENT (comunicação proibida)
  └─ jogadores alternam colocando 1 dado por vez até 8 dados colocados                 R-TURN-*
  └─ cada colocação: valida → aplica café → coloca → resolve efeito imediato do slot
       ├─ Eixo: resolve quando o 2º dado do eixo é colocado                            R-AXI-*
       ├─ Motores: resolve quando o 2º dado dos motores é colocado (avanço)            R-ENG-*
       ├─ Rádio: remove tráfego no espaço indicado                                     R-RAD-*
       ├─ Trem / Flaps / Freios: ativa switch, move marcador                           R-GEA/FLA/BRK-*
       └─ Café: ganha token                                                            R-COF-*
  └─ a qualquer momento previsto: UseRerollAction → decisão pendente para cada jogador  R-RER-*
  └─ após cada resolução: check_loss_conditions()
ROUND_END
  └─ verifica slots obrigatórios                                                       R-TURN-*
  └─ se era a última rodada: LANDING → avalia requisitos de pouso → WON/LOST            R-LND-*
  └─ senão: limpa dados dos slots não persistentes, desce a altitude, alterna 1º jogador R-ALT-*
GAME_OVER
```

O orquestrador (`core/game.py`) só sequencia fases; cada passo chama a mecânica correspondente.
O fim da partida nunca é `if landing: win = True`: é o resultado de `LandingRequirement`s avaliados sobre o estado.

---

## 6. Estratégia para informação oculta

Em Sky Team o que é oculto é essencialmente **o valor dos dados ainda não colocados do parceiro** (escudo),
e a comunicação é restrita durante a colocação.

- O estado completo guarda tudo. `get_observation(player)` aplica uma **política de visibilidade**:
  - dados próprios: valor visível;
  - dados do parceiro na mão: só a *quantidade*, nunca o valor;
  - dados colocados: públicos;
  - RNG: nunca exposto (nem a seed);
  - módulos podem declarar campos privados no próprio estado (`visibility` por campo).
- `get_full_state()` existe para UI de debug, testes e replay, nunca entregue a agentes por padrão.
- **Comunicação**: a engine não modela conversa. A fase de estratégia existe como fase explícita, mas sem canal
  de mensagens. Se no futuro quisermos agentes que "combinam" algo no briefing, isso entra como uma camada
  opcional no `ai/`, não na engine.
- Teste de vazamento: para cada fase, verificar que trocar os valores dos dados ocultos do parceiro não muda
  a observação do jogador (propriedade testável automaticamente).
- Para MCTS com informação imperfeita: `determinize(observation, rng)` gera um estado completo plausível
  (re-amostra dados ocultos), base para IS-MCTS.

---

## 7. Estratégia para módulos

```python
class GameModule(ABC):
    id: ClassVar[str]
    def setup(self, ctx: RuleContext, params: dict) -> None: ...           # estado inicial em state.modules[id]
    def extra_slots(self, params) -> list[SlotDef]: ...                     # slots novos no painel
    def hooks(self) -> list[HookRegistration]: ...                          # interceptações de regra
    def handle_event(self, ctx, event: GameEvent) -> None: ...              # reação a eventos
    def legal_actions(self, ctx, player) -> list[Action]: ...               # ações próprias do módulo
    def apply_action(self, ctx, action: ModuleAction) -> None: ...
    def loss_conditions(self) -> list[LossCondition]: ...
    def landing_requirements(self) -> list[LandingRequirement]: ...
    def validate(self, state) -> list[Violation]: ...                       # invariantes próprias
```

- **Hooks de regra** com pontos nomeados e prioridade determinística (ordem estável por `priority, id`):
  `allowed_values(slot, die)`, `slot_owner(slot)`, `engine_advance(sum, markers)`, `traffic_movement`,
  `round_start_effects`, `mandatory_slots`, etc. Cada mecânica pergunta ao hook em vez de usar constante fixa.
- Estado interno do módulo vive em `state.modules[module_id]` (dict serializável), nunca em atributos da
  instância. Instâncias de módulo são **sem estado**; por isso clone/snapshot não precisam saber de módulos.
- Registro por id (`modules/registry.py`); o cenário JSON lista `{"id": "...", "params": {...}}`.
- Expansões registram novos módulos no mesmo registro, sem mudar o core.

---

## 8. Estratégia para habilidades

Mesmo padrão dos módulos, com metadados explícitos exigidos pelo pedido:

```python
class SpecialAbility(ABC):
    id: ClassVar[str]
    usable_by: ClassVar[frozenset[Player]]
    timing: ClassVar[AbilityTiming]       # PLACEMENT_TURN, ON_ROLL, ROUND_END, PASSIVE, ...
    uses: ClassVar[UsesPolicy]            # ONCE_PER_GAME, ONCE_PER_ROUND, PASSIVE, ...
    def can_activate(self, ctx, player) -> list[Violation]: ...
    def legal_targets(self, ctx, player) -> list[tuple]: ...
    def activate(self, ctx, player, params) -> None: ...
    def hooks(self) -> list[HookRegistration]: ...   # habilidades passivas alteram regras por hooks
```

- `UseAbilityAction(ability_id, params)` é validada como qualquer ação. Habilidades que pedem escolha do outro
  jogador empilham uma `PendingDecision`.
- Interação entre habilidades/módulos resolvida pela ordem determinística de hooks e documentada por teste.
- Quantas habilidades o cenário permite e como são escolhidas sai do JSON do cenário (regra a confirmar).

---

## 9. Estrutura dos dados dos cenários

Três níveis, para não duplicar dados (um aeroporto pode ter várias pistas/cenários):

```jsonc
// data/airports/XXX.json
{ "code": "XXX", "name": "...", "country": "...", "tracks": ["XXX-a", "XXX-b"] }

// data/approach_tracks/XXX-a.json
{ "id": "XXX-a", "airport": "XXX",
  "spaces": [ {"traffic": 0}, {"traffic": 1}, ..., {"airport": true} ],
  "notes": "TODO_RULE_VERIFICATION" }

// data/altitude_tracks/<id>.json
{ "id": "...", "spaces": [ {"altitude": 6000, "reroll": false, "icons": []}, ... ] }

// data/scenarios/<id>.json
{ "id": "...", "airport": "XXX", "approach_track": "XXX-a", "altitude_track": "...",
  "difficulty": "...", "label": "...",
  "modules": [ {"id": "...", "params": {}} ],
  "special_abilities": {"count": 0, "pool": "base"},
  "setup_overrides": {},
  "source": {"manual": "...", "page": 0},
  "verified": false }
```

- Cada arquivo carrega `source` (manual e página) e `verified`. Um cenário com `verified: false` pode ser jogado
  em modo debug, mas aparece marcado na tela de seleção e na matriz de cobertura.
- Validação no load: ids referenciados existem, pista termina em aeroporto, contagens não negativas,
  módulos existem no registro, parâmetros conferem com o esquema do módulo.
- O card da tela de seleção é derivado inteiramente desses dados (código, nome, dificuldade, tráfego,
  módulos, nº de habilidades).

---

## 10. API proposta para IA

Engine (seções 5, 10, 24, 33):

```python
game = SkyTeamGame(scenario_id, registry)
game.reset(seed=42)
game.get_full_state(); game.get_observation(p); game.get_action_mask(p)
game.get_legal_actions(p); game.is_action_legal(a); game.explain_illegal_action(a)
game.step(a) -> StepResult     # = apply_action + eventos emitidos
game.undo_action(); game.clone(); game.save_state(); game.load_state(snap)
game.is_terminal(); game.get_result(); game.history; game.events
```

Ambiente (`ai/`), sem dependência de Gymnasium:

```python
env = SkyTeamEnv(scenario="...", seed=42, reward=SparseReward())
obs = env.reset()
obs, mask = env.observe(player)
obs, reward, terminated, truncated, info = env.step(action_index)
```

- `get_structured_observation(player)` → dict; `get_vector_observation(player)` → `list[float]` com layout
  documentado em `docs/ai_environment.md` (one-hot para enums, normalização por máximos do registro,
  dados próprios ordenados por valor, contagem de dados ocultos do parceiro).
- Multi-agente: `env.current_player`; o env não sabe se quem joga é humano ou IA. Adapters
  (Gymnasium/PettingZoo AEC) ficam em `ai/adapters/` e são opcionais.
- Recompensa só em `ai/rewards.py` (`SparseReward`: +1/−1/0; interface `RewardFn(prev_state, action, state)`
  para recompensas auxiliares futuras).

---

## 11. Estrutura de diretórios

Ajustes em relação à proposta do pedido, com motivo:

```
skyteam/
  core/        game.py state.py actions.py rules.py dice.py rng.py validation.py events.py hooks.py
               phases.py visibility.py serialization.py enums.py exceptions.py
  mechanics/   axis.py engines.py radio.py landing_gear.py flaps.py brakes.py concentration.py
               altitude.py approach.py traffic.py rerolls.py landing.py loss.py
  modules/     base.py registry.py <um arquivo por módulo>
  abilities/   base.py registry.py <um arquivo por habilidade>
  scenarios/   loader.py schema.py registry.py
  data/        airports/ approach_tracks/ altitude_tracks/ scenarios/ panel/ abilities/ modules/
  ai/          environment.py observation.py action_space.py action_mask.py rewards.py adapters/
  replay/      replay.py
  simulate.py  benchmark.py
  ui/          (somente Etapa 12) screens/ widgets/ assets/ renderer.py
tests/         (fora do pacote, como manda o pytest moderno)
docs/
main.py
```

- `rng.py`, `hooks.py`, `phases.py`, `visibility.py`, `serialization.py` saíram de `game.py` para manter
  arquivos pequenos e responsabilidades separadas.
- `mechanics/rerolls.py`, `landing.py`, `loss.py`: rerolls, pouso e derrotas são regras próprias, centralizadas.
- `data/approach_tracks` e `data/altitude_tracks` separados de `airports` porque são reutilizados por cenários.
- `data/panel/` descreve os slots do painel base (dono, valores permitidos, ordem), consumidos pelas mecânicas.

---

## 12. Plano de testes

- **Unitários por mecânica** (`test_axis.py`, `test_engines.py`, ... lista da seção 27), construindo estados
  mínimos com um builder (`StateBuilder().with_axis(1).with_dice(...)`) em vez de jogar partidas inteiras.
- **Legalidade**: para cada violação conhecida, um teste que confirma a mensagem de `explain_illegal_action`.
- **Propriedades** (sem dependência extra; laços com seeds): em partidas aleatórias,
  `validate_state()` sempre passa; toda ação de `get_legal_actions` é aceita por `step`; nenhuma ação fora dela é;
  máscara ↔ lista de ações legais são equivalentes; `from_dict(to_dict(s)) == s`; `clone` não compartilha
  estado mutável; `undo` restaura exatamente o estado anterior.
- **Determinismo**: duas partidas com mesma seed/ações produzem históricos idênticos; replay de partidas
  gravadas reproduz o resultado.
- **Informação oculta**: teste de vazamento descrito na seção 6.
- **Cenários de ponta a ponta**: partidas roteirizadas (dados fixados no debug) para pouso bem-sucedido e
  **uma partida por condição de derrota**.
- **Dados**: todo JSON de `data/` carrega e valida; todo cenário roda 100 partidas aleatórias sem erro.
- **Rastreabilidade**: cada teste de regra referencia o id da regra (`R-AXI-02`) em um marcador pytest; um teste
  gera/confere a matriz de cobertura a partir desses marcadores.

---

## 13. Etapas de implementação

Seguindo a seção 39, com um critério de saída por etapa:

| Etapa | Entrega | Critério de saída |
|---|---|---|
| 1. Análise | Registro de regras com ids, fonte e status | Toda regra com página do manual; pendências listadas |
| 2. Arquitetura | `docs/architecture.md`, enums, dataclasses, interfaces sem lógica | Revisão sua antes de seguir |
| 3. Core | estado, RNG, fases, ações, validação, serialização | testes de serialização/determinismo verdes |
| 4. Mecânicas | uma por vez, com testes | matriz atualizada por mecânica |
| 5. Vitória/derrota | `landing.py`, `loss.py` | um teste por condição |
| 6. Cenário básico | primeiro cenário de ponta a ponta | partidas roteirizadas vencendo e perdendo |
| 7. Módulos | um por vez | teste por módulo + interação |
| 8. Habilidades | uma por vez | teste por habilidade |
| 9. Todos os cenários | JSON de todos, `verified: true` | carregam e rodam 100 partidas cada |
| 10. API de IA | env, observação, máscara, replay, snapshots | testes de máscara e vazamento |
| 11. Simulador | `python -m skyteam.simulate`, benchmark | meta de partidas/segundo registrada |
| 12. Interface | Pygame | UI só usa a API pública |

---

## 14. Pontos das regras a extrair/confirmar nos manuais

Lista completa e numerada em [`docs/etapa1/pendencias_regras.md`](etapa1/pendencias_regras.md).
Os que mais afetam a arquitetura:

1. Quem coloca o primeiro dado em cada rodada (sempre o Piloto ou alternado) e se a alternância é estrita.
2. Momento exato e escopo do reroll (quem pode pedir, quais dados podem ser rolados de novo, se o parceiro decide).
3. Café: quando pode ser gasto, se pode mudar o valor em mais de 1 por dado, limites 1 e 6, máximo de tokens.
4. Eixo: limite exato que causa derrota e se a resolução é imediata.
5. Motores: regra exata de comparação com os marcadores (estrito ou não), comportamento no espaço do aeroporto
   e na última rodada.
6. Tráfego: colisão ao *entrar* ou ao *passar* por espaço com avião; o que acontece ao ultrapassar o aeroporto.
7. Rádio: como o valor do dado mapeia para o espaço-alvo (1 = espaço atual?).
8. Valores permitidos de cada switch de trem, flaps e freios, e ordem obrigatória.
9. Slots obrigatórios por rodada e a consequência de não preenchê-los.
10. Requisitos completos do pouso e o que acontece se o avião chega ao aeroporto antes da última rodada.
11. Lista oficial de aeroportos, pistas, cenários e dificuldades da caixa base.
12. Lista oficial de módulos e habilidades da caixa base, com texto de efeito, momento e reutilização.
