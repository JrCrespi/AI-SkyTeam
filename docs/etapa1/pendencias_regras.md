# Pendências de regras (TODO_RULE_VERIFICATION)

Depois da leitura dos manuais oficiais em inglês (MB = *Landing Procedure*, RV = *Flight Log*), sobram dois tipos de pendência:

- **Componente**: o dado está impresso numa peça física que não está nos PDFs. Uma foto resolve.
- **Interpretação**: o texto permite mais de uma leitura. Proponho um padrão, que a engine deixa configurável.

Ids referem-se a [`regras_extraidas.md`](regras_extraidas.md).

## A. Componentes que faltam (fotos necessárias)

| # | O que falta | Usado em | Regras |
|---|---|---|---|
| P12 | **As pistas de aproximação** de todos os cenários (as duas faces de cada carta/tira): número de espaços, ícones de tráfego por espaço, ícones de dado de Tráfego e posições permitidas do eixo (Curvas). Precisa também da faixa colorida, para casar a pista com o cenário. | `data/approach_tracks/` | R-APP-07, R-SET-07, R-TRD-*, R-TRN-05 |
| P12b | **O outro lado da trilha de altitude** (cenários vermelhos e pretos): espaços, rerrolagens e setas. O lado verde/amarelo já foi recebido. | `data/altitude_tracks/` | R-ALT-02 |
| P14 | Faces do **dado de Tráfego**. | `modules/traffic_dice.py` | R-TRD-07 |
| P16 | **Trilha de Querosene**: numeração completa e posição do X. | `modules/kerosene.py` | R-KER-05 |
| P17 | **Fichas de Estagiário**: o conjunto completo da caixa. A placa tem 5 espaços (ilustração RV p.4). | `modules/intern.py` | R-INT-09 |
| P18 | **Anel de Vento**: valor de cada espaço e o que acontece nos extremos. | `modules/wind.py` | R-WND-04 |
| P20 | **Cartas de Habilidade Especial**: o Flight Log só reproduz Mastery e Synchronisation. Faltam as demais. | `abilities/` | R-ABL-06 |
| P21 | Painel de controle: foto aproximada do disco do eixo (marcas e X), da escala de velocidade e da pista de freio, para confirmar o que foi lido nas ilustrações. | `data/panel/base.json` | R-AXI-05, R-ENG-05, R-BRK-05, R-GEA-01, R-FLA-01 |


## B. Interpretações (padrão proposto)

| # | Dúvida | Onde interfere | Padrão proposto | Configurável em |
|---|---|---|---|---|
| P2 | **Impossível no jogo base** (prova em `docs/architecture.md`, teste em `test_invariants.py`); continua relevante para módulos que mudam o painel. O jogador da vez não tem nenhuma colocação legal, porque todos os espaços livres rejeitam todos os seus valores, mesmo com café. O manual não trata disso. | `get_legal_actions`, fluxo | Ação `DiscardDieAction`: o dado é descartado sem efeito, e a obrigatoriedade (R-MAND-02) decide o resultado no fim da rodada. A dica estratégica do MB p.12 chama de "descartar" o ato de colocar um dado na Concentração, o que sugere que não existe descarte livre. Por isso o descarte só fica disponível quando nada mais é legal. Isso só acontece com a Concentração e o Rádio da cor do jogador já ocupados. | `rules.no_legal_placement` |
| P3 | Rerrolagem "a qualquer momento" e "por qualquer jogador" num jogo por turnos digital. | `mechanics/rerolls.py`, env de IA | Antes de cada colocação, o jogador da vez pode rerrolar. Além disso, existe uma janela de reação em que o outro jogador também pode (pulada automaticamente sem fichas no estoque). Cada jogador escolhe, em sequência, quais dados relança. | `rules.reroll_windows` |
| P4 | Concentração com 3 cafés: é permitido colocar o dado sem ganhar o token? | `concentration.py` | Permitido, sem ganho. O texto limita a quantidade de tokens, não o espaço. | `rules.concentration_when_full` |
| P7 | Avançar 2 quando o 1º espaço de destino tem tráfego. | `approach.py` | Avanço passo a passo, com verificação de colisão em cada passo (R-APP-04). Assim o 2º passo colide. | não configurável: decorre do texto |
| P8 | Rádio com valor além do Aeroporto. | `radio.py` | Legal e sem efeito (R-RAD-03). | — |
| P9 | Dado em Flap já acionado. | `flaps.py` | Legal e sem efeito, por analogia com o trem (MB p.7). | `rules.flap_reuse` |
| P10a | Freio após o 1º acionamento: marcador entre 2 e 3? | `data/panel/base.json` | Tabela em dados: `[1.5, 2.5, 4.5, 6.5]` como "velocidade deve ser menor que". Confirmar pela foto (P21). | dados |
| P10b | **Só nos Freios de Gelo.** No jogo base, o texto em inglês resolve a dúvida: a velocidade é comparada com os freios no momento do 2º dado do Motor (R-BRK-07). Os Freios de Gelo dizem "at the end of the last round, your Speed must be lower than the Brake marker". | `ice_brakes.py` | Mesmo momento do jogo base. A frase dos Freios de Gelo foi lida como uma repetição da condição D, não como uma regra nova. | `ice_brakes.brake_check` |
| P15 | Curvas: em qual espaço se verifica o eixo ao avançar? O inglês diz "not in one of the permitted positions in the Current Position screen" e "also applies to both spaces you fly through if you advance 2". | `modules/turns.py` | No espaço **de saída** de cada passo (Posição Atual antes de mover). Assim, avançando 2, verificam-se a posição inicial e o espaço intermediário. | `turns.check_space` |
| P17b | Estagiário: colocar a ficha é imediato (ação extra) ou é a jogada do próximo turno? | `intern.py` | Imediato no mesmo turno ("Você pode então colocar essa ficha"). A ficha guardada não persiste. | `intern.token_timing` |
| P18b | Vento: se o Motor for resolvido antes do Eixo, qual posição vale? | `wind.py` | A posição atual da ficha (que ainda reflete a rodada anterior). | — |
| P19 | Freios de Gelo: os dois dados precisam ter o valor impresso no espaço? E quem pode jogar em cada fileira? A de cima é azul; a de baixo parece azul e laranja. | `ice_brakes.py` | O valor é igual ao número do espaço. Cima: só o Piloto. Baixo: qualquer jogador, pela cor da ilustração. Confirmar pela foto. | dados |
| P20b | Habilidades: quem escolhe as cartas e quando. | `abilities/`, setup | Escolhidas no setup, antes da 1ª rodada, pelos dois jogadores juntos (é jogo cooperativo e a escolha é pública). | — |
| P23 | Mastery: "only if a Reroll token is available". Disponível onde? Na caixa (o jogo tem 2 fichas) ou ainda não colocada na trilha de altitude? | `abilities/mastery.py` | Disponível = ficha que não está nem no estoque do painel nem na trilha de altitude, isto é, já gasta e devolvida. Há no máximo 2 fichas em jogo. | `mastery.token_source` |
| P24 | Synchronisation: "placed at least one die on Landing Gear and one die on Flaps" vale **nesta rodada** ou no jogo? Pode ser usada mais de uma vez? Quem dispara? | `abilities/synchronisation.py` | Nesta rodada, uma vez por rodada, disparada automaticamente assim que a condição é cumprida ("immediately"). O dado de Tráfego é colocado pelo jogador que completou a condição. | `synchronisation.*` |
| P22 | Tempo Real na engine headless: a engine não tem relógio. | `real_time.py`, env | A engine recebe `TimeExpiredAction` (sistema). A UI dispara essa ação após 60 s. Na simulação, um `TimePolicy` (por exemplo, um número máximo de colocações) a dispara. | `real_time.policy` |

Cada padrão acima entra no código com `TODO_RULE_VERIFICATION` e a referência `P<n>`, e um teste fixa o comportamento.
Se você discordar de algum, a mudança é de configuração, não de arquitetura.
