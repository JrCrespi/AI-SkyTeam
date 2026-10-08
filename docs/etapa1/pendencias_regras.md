# Pendências de regras (TODO_RULE_VERIFICATION)

Cada item: qual regra está em dúvida, onde ela interfere na implementação, e como a arquitetura vai suportar
qualquer resposta sem inventar comportamento. Ids referem-se a `regras_extraidas.md`.

| # | Regra | Onde interfere | Suporte arquitetural enquanto não confirmada |
|---|---|---|---|
| P1 | R-TURN-02 / R-ALT-03: primeiro jogador da rodada | `core/phases.py`, ordem de turnos, observação | `first_player_policy` em dados do cenário/regras base |
| P2 | R-TURN-03/05: obrigatoriedade de colocar todos os dados e consequência de não conseguir | `get_legal_actions`, `mechanics/loss.py` | `MandatorySlotsPolicy` por hook; `LossReason.MANDATORY_SLOT_UNFILLED` reservado |
| P3 | R-RER-02/03/04: quem dispara, escopo, momento e expiração do reroll | `mechanics/rerolls.py`, `PendingDecision` | Decisão pendente por jogador; parâmetros (`who_can_trigger`, `expires`) em dados |
| P4 | R-COF-02/03/04/05: máximo de café, ajuste por token, uso múltiplo, espaços | `mechanics/concentration.py`, codificação de ações (`coffee_delta`) | Faixa de `coffee_delta` e máximo vêm de constantes de dados, não do código |
| P5 | R-AXI-03/04: momento da resolução e limite do eixo | `mechanics/axis.py`, `LossReason.AXIS_*` | Limite lido de `data/panel/base.json`; momento via `ResolutionTrigger` do slot |
| P6 | R-ENG-03/04: comparação com marcadores (estrita/inclusiva) e momento | `mechanics/engines.py` | Função `engine_advance` como hook, comparador configurável em dados |
| P7 | R-APP-02/03/04: colisão (entrar × passar), ultrapassar aeroporto, chegar cedo | `mechanics/approach.py`, `mechanics/loss.py` | Movimento passo a passo com evento por espaço, permitindo qualquer das regras |
| P8 | R-RAD-01/02/03: nº de espaços de rádio, mapeamento valor→espaço, rádio sem alvo | `mechanics/radio.py`, `data/panel/base.json` | Offset do mapeamento e legalidade sem alvo em dados |
| P9 | R-GEA-01/02, R-FLA-01, R-BRK-01: valores e ordem dos switches | `data/panel/base.json` | Slots declaram `allowed_values` e `requires` (ordem) em dados |
| P10 | R-BRK-03, R-LND-06: comparação velocidade × frenagem | `mechanics/landing.py` | `LandingRequirement` com comparador configurável |
| P11 | R-COM-03: o que é permitido falar no briefing | Apenas documentação/IA (engine não modela fala) | Sem impacto na engine |
| P12 | Lista de aeroportos, pistas, esteiras de altitude e cenários | `data/` inteiro, tela de seleção | Loader e esquema prontos; arquivos só entram com página de origem |
| P13 | Lista de módulos e seus efeitos | `modules/` | Interface `GameModule` + hooks; um arquivo por módulo depois da extração |
| P14 | Lista de habilidades especiais, quantidade por cenário, escolha | `abilities/`, cenário JSON | Interface `SpecialAbility` + `special_abilities.count` no cenário |

## O que preciso do manual

1. PDF (ou fotos legíveis) do livro de regras da caixa base.
2. Material dos cenários: lista de aeroportos e as pistas de aproximação impressas (tráfego por espaço,
   esteira de altitude, módulos indicados), se não estiverem no livro.
3. Textos das cartas de habilidades e dos módulos, ou as páginas que os descrevem.

Com isso cada linha acima vira `CONFIRMADA (p. N)` ou `CORRIGIDA (p. N)`.
