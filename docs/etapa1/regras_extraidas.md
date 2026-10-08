# Etapa 1: registro de regras (rascunho, aguardando manuais)

## Como ler este documento

Os manuais oficiais **ainda não foram fornecidos** ao projeto. Este registro foi montado a partir de
conhecimento prévio do jogo, para já estruturar a extração. Por isso:

- **Nenhuma regra aqui é fonte de verdade.** Todas estão com status `TODO_RULE_VERIFICATION` até serem
  conferidas com o manual e receberem a página de origem.
- A coluna **Confiança** indica o quanto confio na minha lembrança: **A** (alta, regra central do jogo),
  **M** (média, provável mas com detalhe incerto), **B** (baixa, apenas um nome ou uma suspeita).
- Nada com confiança M ou B será codificado como comportamento; vira ponto de extensão com `TODO_RULE_VERIFICATION`.
- Dados numéricos de aeroportos, pistas e cenários **não** foram preenchidos: não tenho como reproduzi-los
  com segurança e o pedido proíbe inventar.

Cada regra tem um id estável (`R-<área>-<nn>`), que será citado no código, nos testes e em `rules_mapping.md`.

Status possíveis: `PENDENTE` (aguardando manual) · `CONFIRMADA (p. N)` · `CORRIGIDA (p. N)` · `AMBÍGUA`.

---

## 1. Componentes e papéis

| Id | Regra (como entendo hoje) | Conf. | Status |
|---|---|---|---|
| R-GEN-01 | Jogo cooperativo para 2 jogadores: Piloto e Copiloto. | A | PENDENTE |
| R-GEN-02 | Cada jogador tem 4 dados de 6 faces de sua cor (Piloto azul, Copiloto laranja). | A | PENDENTE |
| R-GEN-03 | Cada jogador rola seus dados escondidos atrás de um escudo; o parceiro não vê os valores. | A | PENDENTE |
| R-GEN-04 | O painel tem espaços exclusivos do Piloto, exclusivos do Copiloto e espaços de qualquer jogador. | A | PENDENTE |
| R-GEN-05 | A partida dura um número fixo de rodadas definido pela esteira de altitude; a última rodada é a de pouso. | A | PENDENTE |

## 2. Comunicação e fases

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-COM-01 | Antes de rolar os dados há uma fase de briefing/estratégia em que os jogadores podem conversar livremente. | A | PENDENTE |
| R-COM-02 | Depois que os dados são rolados, é proibido comunicar valores ou intenções (verbalmente ou por gestos). | A | PENDENTE |
| R-COM-03 | Limites exatos do que pode ser dito no briefing (pode falar de valores hipotéticos?). | B | PENDENTE |
| R-TURN-01 | Na fase de colocação os jogadores alternam, colocando um dado por vez. | A | PENDENTE |
| R-TURN-02 | Quem coloca o primeiro dado em cada rodada (sempre o Piloto? alterna?). | M | PENDENTE |
| R-TURN-03 | Todos os 8 dados devem ser colocados a cada rodada; um jogador não pode passar. | M | PENDENTE |
| R-TURN-04 | Eixo e Motores são obrigatórios: cada jogador deve colocar um dado em cada um a cada rodada. | A | PENDENTE |
| R-TURN-05 | Consequência de não ser possível preencher os obrigatórios (derrota? colocação forçada?). | B | PENDENTE |
| R-TURN-06 | Ao fim da rodada, os dados voltam para os jogadores; switches ativados (trem, flaps, freios) permanecem. | A | PENDENTE |

## 3. Dados e rerolls

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-DIE-01 | Os dados são rolados uma vez por rodada, no início da colocação. | A | PENDENTE |
| R-DIE-02 | Um dado colocado não pode ser movido nem relançado. | A | PENDENTE |
| R-RER-01 | Alguns espaços da esteira de altitude concedem um token de reroll ao serem alcançados. | A | PENDENTE |
| R-RER-02 | Ao usar um reroll, cada jogador pode relançar qualquer quantidade de seus dados ainda não colocados. | M | PENDENTE |
| R-RER-03 | Quem pode iniciar o reroll, quando (no próprio turno?) e se o token expira ao fim da rodada. | B | PENDENTE |
| R-RER-04 | Quantidade máxima de tokens de reroll acumulados. | B | PENDENTE |

## 4. Eixo (Axis)

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-AXI-01 | O eixo tem um espaço do Piloto e um do Copiloto; ambos obrigatórios a cada rodada. | A | PENDENTE |
| R-AXI-02 | Quando os dois dados estão colocados, o avião inclina para o lado do dado de maior valor, um passo por ponto de diferença. Valores iguais: sem mudança. | A | PENDENTE |
| R-AXI-03 | A resolução ocorre imediatamente ao colocar o segundo dado do eixo. | M | PENDENTE |
| R-AXI-04 | Se a inclinação ultrapassa o limite do indicador, a partida é perdida (avião capota). Valor exato do limite. | M | PENDENTE |
| R-AXI-05 | No pouso o eixo precisa estar nivelado. | A | PENDENTE |

## 5. Motores (Engines) e aproximação

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-ENG-01 | Motores têm um espaço do Piloto e um do Copiloto; ambos obrigatórios. | A | PENDENTE |
| R-ENG-02 | A velocidade é a soma dos dois dados. | A | PENDENTE |
| R-ENG-03 | Soma abaixo do marcador azul: o avião não avança; entre azul e laranja: avança 1; acima do laranja: avança 2. Comparação estrita ou inclusiva? | M | PENDENTE |
| R-ENG-04 | A resolução ocorre ao colocar o segundo dado dos motores. | M | PENDENTE |
| R-ENG-05 | Na rodada de pouso a soma dos motores não move o avião: é comparada à capacidade de frenagem. | A | PENDENTE |
| R-APP-01 | A pista de aproximação é uma sequência de espaços que termina no aeroporto; cada espaço pode ter aviões (tráfego). | A | PENDENTE |
| R-APP-02 | O avião não pode entrar/passar por um espaço com tráfego: isso é colisão e derrota. Entrar × passar? | M | PENDENTE |
| R-APP-03 | O avião não pode ultrapassar o aeroporto. Consequência: derrota? | M | PENDENTE |
| R-APP-04 | Chegar ao aeroporto antes da última rodada: o que acontece com rodadas restantes. | B | PENDENTE |
| R-APP-05 | Para o pouso, o avião deve estar no espaço do aeroporto e não pode restar tráfego na pista. | A | PENDENTE |

## 6. Rádio e tráfego

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-RAD-01 | Piloto tem 1 espaço de rádio; Copiloto tem 2. | M | PENDENTE |
| R-RAD-02 | O valor do dado indica a distância do espaço-alvo na pista (1 = espaço atual do avião?), e remove um avião daquele espaço. | M | PENDENTE |
| R-RAD-03 | Se não há avião no espaço-alvo, o dado é colocado sem efeito (é permitido?). | B | PENDENTE |
| R-TRF-01 | Tráfego inicial vem impresso na pista de aproximação de cada cenário. | A | PENDENTE |
| R-TRF-02 | Há módulos em que o tráfego se move ou é adicionado durante a partida. | B | PENDENTE |

## 7. Trem de pouso, flaps e freios

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-GEA-01 | Trem de pouso: 3 switches exclusivos do Piloto, cada um com faixa de valores própria. Valores exatos. | M | PENDENTE |
| R-GEA-02 | Ordem: os 3 switches do trem podem ser ativados em qualquer ordem? | B | PENDENTE |
| R-GEA-03 | Cada switch ativado move o marcador aerodinâmico azul um passo (aumenta a velocidade mínima). | A | PENDENTE |
| R-GEA-04 | No pouso os 3 switches devem estar ativados. | A | PENDENTE |
| R-FLA-01 | Flaps: 4 switches exclusivos do Copiloto, ativados em ordem fixa, cada um com faixa de valores. Valores exatos. | M | PENDENTE |
| R-FLA-02 | Cada flap ativado move o marcador aerodinâmico laranja um passo. | A | PENDENTE |
| R-FLA-03 | No pouso os 4 flaps devem estar ativados. | A | PENDENTE |
| R-BRK-01 | Freios: 3 espaços exclusivos do Piloto, ativados em ordem, cada um exige um valor específico. Valores exatos. | M | PENDENTE |
| R-BRK-02 | Cada freio ativado avança o marcador vermelho de frenagem. | A | PENDENTE |
| R-BRK-03 | No pouso, a soma dos motores deve ser menor que o valor do marcador de frenagem (estrito?). | M | PENDENTE |

## 8. Concentração / café

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-COF-01 | Há espaços de concentração que aceitam um dado de qualquer valor e de qualquer jogador; cada um gera um token de café. | M | PENDENTE |
| R-COF-02 | Tokens de café são compartilhados entre os jogadores, com máximo (3?). | M | PENDENTE |
| R-COF-03 | Gastar um token ajusta em ±1 o valor de um dado no momento de colocá-lo; vários tokens no mesmo dado? | M | PENDENTE |
| R-COF-04 | O ajuste não dá a volta (6 não vira 1). | M | PENDENTE |
| R-COF-05 | Quantidade de espaços de concentração e se ficam bloqueados após o uso na rodada. | B | PENDENTE |

## 9. Altitude

| Id | Regra | Conf. | Status |
|---|---|---|---|
| R-ALT-01 | A esteira de altitude marca a rodada atual e desce um espaço ao fim de cada rodada. | A | PENDENTE |
| R-ALT-02 | Espaços específicos concedem reroll (ver R-RER-01). | A | PENDENTE |
| R-ALT-03 | Indica quem é o primeiro jogador da rodada? (ligado a R-TURN-02) | B | PENDENTE |
| R-ALT-04 | Ao atingir o último espaço (solo) sem condições de pouso, a partida é perdida. | A | PENDENTE |

## 10. Pouso (vitória)

Hipótese atual: a partida é vencida se, ao fim da rodada final, **todas** as condições abaixo valem.

| Id | Condição | Conf. | Status |
|---|---|---|---|
| R-LND-01 | Avião no espaço do aeroporto. | A | PENDENTE |
| R-LND-02 | Nenhum avião (tráfego) na pista de aproximação. | A | PENDENTE |
| R-LND-03 | Eixo nivelado. | A | PENDENTE |
| R-LND-04 | Todos os switches do trem de pouso ativados. | A | PENDENTE |
| R-LND-05 | Todos os flaps ativados. | A | PENDENTE |
| R-LND-06 | Velocidade (soma dos motores) menor que a capacidade de frenagem. | M | PENDENTE |
| R-LND-07 | Condições extras impostas por módulos do cenário. | M | PENDENTE |

## 11. Derrota

| Id | Condição | Conf. | Status |
|---|---|---|---|
| R-LOSS-01 | Inclinação do eixo além do limite. | A | PENDENTE |
| R-LOSS-02 | Colisão com tráfego na aproximação. | A | PENDENTE |
| R-LOSS-03 | Ultrapassar o aeroporto. | M | PENDENTE |
| R-LOSS-04 | Fim da altitude sem estar no aeroporto. | A | PENDENTE |
| R-LOSS-05 | Qualquer condição de pouso (R-LND-*) falha na rodada final. | A | PENDENTE |
| R-LOSS-06 | Slots obrigatórios não preenchidos (ver R-TURN-05). | B | PENDENTE |
| R-LOSS-07 | Derrotas específicas de módulos (ex.: combustível acabar). | B | PENDENTE |

## 12. Aeroportos e cenários

**Não extraído.** Necessário o material da caixa (pistas de aproximação impressas e o manual).

Para cada cenário serão extraídos estes campos (template em `docs/00_analise_tecnica.md`, seção 9):
código do aeroporto, nome, pista/lado, dificuldade, esteira de altitude, tráfego por espaço, módulos,
nº de habilidades, regras particulares, página/fonte.

Lembrança com confiança baixa, só para orientar a busca no manual: o primeiro cenário/tutorial seria
em Montréal (YUL). Nenhum outro aeroporto será listado antes de conferir.

## 13. Módulos e habilidades especiais

**Não extraído.** Sei que a caixa base traz módulos avançados e cartas de habilidades especiais, mas não
tenho segurança suficiente sobre nomes, quantidade e efeitos para listá-los aqui sem arriscar inventar.

Para cada módulo/habilidade serão extraídos: nome, cenários que usam, componentes, setup, novos espaços no
painel, alteração de regras, momento de efeito, quem usa, alvos, duração, reutilização, novas condições de
derrota ou pouso, interações conhecidas e página.

---

## Regras compartilhadas × específicas

- **Compartilhadas** (todo cenário): seções 1 a 11 acima. Implementadas uma vez em `core/` e `mechanics/`.
- **Específicas**: tráfego inicial, tamanho da pista, esteira de altitude, módulos e habilidades.
  Entram exclusivamente como dados de cenário e plugins.
