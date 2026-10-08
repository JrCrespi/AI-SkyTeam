# Pendências de regras (TODO_RULE_VERIFICATION)

Depois da leitura do manual base (MB) e do Registro de Voo (RV), sobram dois tipos de pendência:

- **Componente**: o dado está impresso numa peça física que não está nos PDFs. Uma foto resolve.
- **Interpretação**: o texto permite mais de uma leitura. Proponho um padrão, que a engine deixa configurável.

Ids referem-se a [`regras_extraidas.md`](regras_extraidas.md).

## A. Componentes que faltam (fotos necessárias)

| # | O que falta | Usado em | Regras |
|---|---|---|---|
| P12 | **As pistas de aproximação** de todos os cenários (as duas faces de cada carta/tira): número de espaços, ícones de tráfego por espaço, ícones de dado de Tráfego e posições permitidas do eixo (Curvas). Precisa também da faixa colorida, para casar a pista com o cenário. | `data/approach_tracks/` | R-APP-07, R-SET-07, R-TRD-*, R-TRN-05 |
| P12b | **As trilhas de altitude** (frente e verso): espaços, ícones de rerrolagem e a seta de primeiro jogador em cada espaço. | `data/altitude_tracks/` | R-TURN-02, R-RER-05, R-ALT-01/02 |
| P14 | Faces do **dado de Tráfego**. | `modules/traffic_dice.py` | R-TRD-07 |
| P16 | **Trilha de Querosene**: numeração completa e posição do X. | `modules/kerosene.py` | R-KER-05 |
| P17 | **Placa e fichas de Estagiário**: quantas fichas, quais números e quantos espaços. A ilustração do RV mostra 6, 7(?), 3, 5 e 1 entre dois espaços de dado. | `modules/intern.py` | R-INT-08 |
| P18 | **Anel de Vento**: valor de cada espaço e o que acontece nos extremos. | `modules/wind.py` | R-WND-04 |
| P20 | **Cartas de Habilidade Especial**: todas, com o texto legível. | `abilities/` | R-ABL-03/04 |
| P21 | Painel de controle: foto aproximada do disco do eixo (marcas e X), da escala de velocidade e da pista de freio, para confirmar o que foi lido nas ilustrações. | `data/panel/base.json` | R-AXI-05, R-ENG-05, R-BRK-05, R-GEA-01, R-FLA-01 |

Se você tiver o Registro de Voo **original** (inglês ou francês), ele também ajuda: a tradução atual tem trechos truncados.

## B. Interpretações (padrão proposto)

| # | Dúvida | Onde interfere | Padrão proposto | Configurável em |
|---|---|---|---|---|
| P2 | O jogador da vez não tem nenhuma colocação legal, porque todos os espaços livres rejeitam todos os seus valores, mesmo com café. O manual não trata disso. | `get_legal_actions`, fluxo | Ação `DiscardDieAction`: o dado é descartado sem efeito, e a obrigatoriedade (R-MAND-02) decide o resultado no fim da rodada. A dica estratégica do MB p.12 chama de "descartar" o ato de colocar um dado na Concentração, o que sugere que não existe descarte livre. Por isso o descarte só fica disponível quando nada mais é legal. Isso só acontece com a Concentração e o Rádio da cor do jogador já ocupados. | `rules.no_legal_placement` |
| P3 | Rerrolagem "a qualquer momento" e "por qualquer jogador" num jogo por turnos digital. | `mechanics/rerolls.py`, env de IA | Antes de cada colocação, o jogador da vez pode rerrolar. Além disso, existe uma janela de reação em que o outro jogador também pode (pulada automaticamente sem fichas no estoque). Cada jogador escolhe, em sequência, quais dados relança. | `rules.reroll_windows` |
| P4 | Concentração com 3 cafés: é permitido colocar o dado sem ganhar o token? | `concentration.py` | Permitido, sem ganho. O texto limita a quantidade de tokens, não o espaço. | `rules.concentration_when_full` |
| P7 | Avançar 2 quando o 1º espaço de destino tem tráfego. | `approach.py` | Avanço passo a passo, com verificação de colisão em cada passo (R-APP-04). Assim o 2º passo colide. | não configurável: decorre do texto |
| P8 | Rádio com valor além do Aeroporto. | `radio.py` | Legal e sem efeito (R-RAD-03). | — |
| P9 | Dado em Flap já acionado. | `flaps.py` | Legal e sem efeito, por analogia com o trem (MB p.7). | `rules.flap_reuse` |
| P10a | Freio após o 1º acionamento: marcador entre 2 e 3? | `data/panel/base.json` | Tabela em dados: `[1.5, 2.5, 4.5, 6.5]` como "velocidade deve ser menor que". Confirmar pela foto (P21). | dados |
| P10b | Condição D (velocidade < freios) é verificada quando o 2º dado do Motor é colocado (MB p.11, "quando você colocou os dados do Motor") ou no fim da rodada (RV p.5, Freios de Gelo)? Isso muda se um freio colocado depois do Motor, na mesma rodada final, conta. | `landing.py` | Fim da rodada final, com os freios finais. O MB p.10 diz "a força dos seus freios deve ser maior que sua velocidade" sem impor ordem, e o RV é explícito. | `rules.landing_brake_check` |
| P13 | Segundo ícone do `TGU_red`. | `data/scenarios/TGU_red.json` | Fica fora até confirmar. | dados |
| P15 | Curvas: em qual espaço se verifica o eixo ao avançar? | `modules/turns.py` | No espaço **de saída** de cada passo (Posição Atual antes de mover), seguindo "na tela Posição Atual". | `turns.check_space` |
| P17b | Estagiário: colocar a ficha é imediato (ação extra) ou é a jogada do próximo turno? | `intern.py` | Imediato no mesmo turno ("Você pode então colocar essa ficha"). A ficha guardada não persiste. | `intern.token_timing` |
| P18b | Vento: se o Motor for resolvido antes do Eixo, qual posição vale? | `wind.py` | A posição atual da ficha (que ainda reflete a rodada anterior). | — |
| P19 | Freios de Gelo: os dois dados precisam ter o valor impresso no espaço? | `ice_brakes.py` | Sim, com valor igual ao número do espaço. | dados |
| P20b | Habilidades: quem escolhe as cartas e quando. | `abilities/`, setup | Escolhidas no setup, antes da 1ª rodada, pelos dois jogadores juntos (é jogo cooperativo e a escolha é pública). | — |
| P22 | Tempo Real na engine headless: a engine não tem relógio. | `real_time.py`, env | A engine recebe `TimeExpiredAction` (sistema). A UI dispara essa ação após 60 s. Na simulação, um `TimePolicy` (por exemplo, um número máximo de colocações) a dispara. | `real_time.policy` |

Cada padrão acima entra no código com `TODO_RULE_VERIFICATION` e a referência `P<n>`, e um teste fixa o comportamento.
Se você discordar de algum, a mudança é de configuração, não de arquitetura.
