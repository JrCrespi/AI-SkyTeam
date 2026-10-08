# Etapa 1: registro de regras

## Fontes

| Sigla | Documento | Páginas |
|---|---|---|
| **MB** | *Landing Procedure* (manual base). Texto de referência: `ST_Rules01_EN_06jun2023.pdf`. Edição PT-BR *Procedimento de Pouso* usada como apoio. | 12 |
| **RV** | *Flight Log* (regras avançadas e cenários). Texto de referência: `ST_Rules02_EN_06jun2023.pdf`. A tradução não oficial *Registro de Voo* foi usada só como apoio. | 8 |

A citação `MB p.5` indica a página impressa no rodapé. A paginação das edições em inglês e em português é a mesma.

**Fonte de verdade: as edições oficiais em inglês.** A tradução PT do Flight Log tem trechos truncados e termos
errados ("TRÁFEGO MORRE" = *Traffic Die*, "VOLTAS" = *Turns*). Toda regra deste registro foi conferida com o texto
em inglês. Quando houve diferença, prevaleceu o inglês. O termo em inglês aparece entre parênteses onde ajuda a
auditar.

## Status

- **CONFIRMADA**: o texto do manual é explícito.
- **ILUSTRAÇÃO**: a regra foi lida de uma ilustração do manual, não do texto. Precisa ser conferida no componente.
- **INFERIDA**: é consequência direta do texto, mas o manual não a afirma literalmente. A justificativa está na linha.
- **AMBÍGUA**: há mais de uma leitura possível. O código usa `TODO_RULE_VERIFICATION`.
- **FALTA COMPONENTE**: o dado está impresso num componente (pista, carta, placa) que não está nos PDFs.

Os ids das regras da versão anterior foram mantidos. Ids novos foram acrescentados.

---

## 1. Visão geral e componentes

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-GEN-01 | Jogo cooperativo para 2 jogadores: Piloto (espaços e dados azuis) e Copiloto (espaços e dados laranja). | MB p.1, p.3 (passo 4) | CONFIRMADA |
| R-GEN-02 | Cada jogador tem 4 dados da sua cor. | MB p.3 | CONFIRMADA |
| R-GEN-03 | Cada jogador tem uma Tela (escudo) que esconde seus dados. | MB p.3 (passo 10), p.4 | CONFIRMADA |
| R-GEN-04 | A partida tem **7 rodadas** de 3 fases: (1) discussão de estratégia e rolagem, (2) alocação de dados, (3) fim da rodada. | MB p.4 | CONFIRMADA |
| R-GEN-05 | Componentes do jogo base: Painel de Controle, 10 interruptores, disco do eixo, 2 marcadores de aerodinâmica (azul e laranja), marcador de freio (vermelho), 12 tokens de Avião, 2 fichas de rerrolagem, 3 tokens de Café, trilha de altitude e pista de aproximação. | MB p.3 | CONFIRMADA |

## 2. Preparação (jogo base)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-SET-01 | O eixo começa horizontal (seta apontando para o triângulo preto), com todos os interruptores nas luzes verdes, ou seja, ainda não acionados. | MB p.3 (1) | CONFIRMADA |
| R-SET-02 | Marcador azul de aerodinâmica entre 4 e 5. Marcador laranja entre 8 e 9. | MB p.3 (2) | CONFIRMADA |
| R-SET-03 | Marcador de freio à esquerda do 2. | MB p.3 (3) | CONFIRMADA |
| R-SET-04 | A trilha de altitude começa em 6000 pés. | MB p.3 (5) | CONFIRMADA |
| R-SET-05 | A pista de aproximação começa na primeira posição (para YUL, o ícone indicado fica visível na tela). | MB p.3 (6) | CONFIRMADA |
| R-SET-06 | Uma ficha de rerrolagem vai em cada ícone de rerrolagem da trilha de altitude. | MB p.3 (7) | CONFIRMADA |
| R-SET-07 | Um token de Avião vai em cada ícone de tráfego impresso em cada espaço da pista de aproximação. | MB p.3 (8) | CONFIRMADA |
| R-SET-08 | Os tokens de Café ficam numa reserva ao lado do tabuleiro, fora dele (0 tokens em jogo). | MB p.3 (9) | CONFIRMADA |

> Nota sobre R-SET-01: na fase de preparação, "luz verde" significa interruptor **coberto**, isto é, ainda não acionado.
> Ao acionar, desliza-se o interruptor para **mostrar** a luz verde (MB p.7). Na engine isso é um booleano `activated`.

## 3. Fase 1: estratégia e rolagem

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-COM-01 | No início de cada rodada os jogadores discutem estratégia livremente. | MB p.4 | CONFIRMADA |
| R-COM-02 | Durante a discussão é proibido falar de valores de dados. Exemplos proibidos: "se você tirar um 6, coloque-o aqui" e "use seu dado mais fraco para...". | MB p.4 | CONFIRMADA |
| R-COM-03 | Depois da discussão, cada jogador rola os 4 dados atrás da Tela. A partir daí, silêncio completo até o fim da rodada, exceto para corrigir erros de regra. | MB p.4 | CONFIRMADA |
| R-DIE-01 | Os dados são rolados uma vez por rodada, nessa fase. | MB p.4 | CONFIRMADA |

## 4. Rerrolagem

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-RER-01 | Se houver uma ficha de rerrolagem no espaço de Altitude Atual, ela vai para o estoque do Painel. Isso inclui a primeira rodada (6000 pés). | MB p.4 | CONFIRMADA |
| R-RER-02 | **A qualquer momento durante a rodada**, **qualquer** jogador pode gastar uma ficha do estoque. | MB p.4, p.9 | CONFIRMADA |
| R-RER-03 | Ao gastar uma ficha, **ambos** os jogadores podem relançar qualquer quantidade (inclusive zero) dos seus dados ainda atrás da Tela, uma única vez. Exemplo: o Piloto relança 2 de 3 e o Copiloto relança os 4. | MB p.4 | CONFIRMADA |
| R-RER-04 | Fichas não gastas permanecem no estoque nas rodadas seguintes. | MB p.4 | INFERIDA: o manual diz "adicione-a ao seu estoque" e não fala em expiração. O jogo tem 2 fichas no total (MB p.3). |
| R-RER-05 | Espaços da trilha base que têm ícone de rerrolagem: **6000** (texto) e mais um, que parece ser **2000**. | MB p.4 (6000), p.3 (ilustração) | 6000 CONFIRMADA; o segundo é ILUSTRAÇÃO |

## 5. Fase 2: alocação de dados (regras gerais)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-TURN-01 | Os jogadores se alternam. | MB p.4 (A) | CONFIRMADA |
| R-TURN-02 | Uma seta na tela de Altitude Atual indica quem joga primeiro na rodada. O Piloto começa a primeira rodada. | MB p.4 (A) | CONFIRMADA. A direção da seta em cada espaço é FALTA COMPONENTE. |
| R-TURN-03 | Na sua vez, o jogador coloca **um e apenas um** dado em um espaço **livre** (sem dado). | MB p.4 (B) | CONFIRMADA |
| R-TURN-04 | Restrição de cor: o Piloto só usa espaços azuis e o Copiloto só usa espaços laranja. Espaços azuis e laranja ao mesmo tempo aceitam os dois. | MB p.4 | CONFIRMADA |
| R-TURN-05 | Restrições numéricas são impressas nos espaços. Exemplo: o 1º Flap só aceita 1 ou 2. | MB p.4 (C, D) | CONFIRMADA |
| R-TURN-06 | Rádio: restrição de cor, sem restrição de número. | MB p.4 (E) | CONFIRMADA |
| R-TURN-07 | Concentração: sem restrição alguma. | MB p.4 (F) | CONFIRMADA |
| R-TURN-08 | A rodada termina depois que os **8 dados** são colocados. | MB p.9 | CONFIRMADA |
| R-TURN-09 | Um jogador não pode passar a vez. | MB p.4 (B), p.9 | INFERIDA de "coloque UM dado" combinado com "depois de colocar todos os 8 dados". |
| R-TURN-10 | Se o jogador da vez não tiver nenhuma colocação legal (todos os espaços livres restringem os valores que ele tem), o que acontece? | | AMBÍGUA (P2) |
| R-DIE-02 | Um dado colocado não é movido nem relançado. | MB p.4 (rerrolagem só para dados atrás da tela) | INFERIDA |

### Ações obrigatórias

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-MAND-01 | Eixo e Motores são obrigatórios. Em cada rodada, cada jogador coloca um dado no Eixo e um nos Motores. | MB p.5 | CONFIRMADA |
| R-MAND-02 | Derrota imediata se, **ao final da rodada**, faltar 1 dado de cada cor no Eixo e 1 dado de cada cor nos Motores. | MB p.5 | CONFIRMADA |
| R-MAND-03 | Os espaços obrigatórios não precisam ser os primeiros a receber dados. | MB p.5 | CONFIRMADA |

## 6. Eixo

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-AXI-01 | Há um espaço de Eixo azul e um laranja. Ambos são obrigatórios. | MB p.5 | CONFIRMADA |
| R-AXI-02 | **Assim que o segundo dado é colocado**, os valores são comparados. Se forem iguais, nada muda. Se forem diferentes, o avião gira tantas marcas quanto a diferença, na direção do jogador que jogou o dado mais alto. | MB p.5 | CONFIRMADA |
| R-AXI-03 | O eixo **não** volta ao centro ao final da rodada. | MB p.5 | CONFIRMADA |
| R-AXI-04 | Se a seta atingir ou passar por um X, o avião entra em giro e a partida é perdida imediatamente. | MB p.5 | CONFIRMADA |
| R-AXI-05 | Posição dos X no disco: a ilustração mostra as marcas 0, 1 e 2 de cada lado e o X em seguida (limite ±2, derrota em ±3). | MB p.5 (ilustração) | ILUSTRAÇÃO |
| R-AXI-06 | Condição de vitória C: o avião está totalmente horizontal (eixo 0) ao final da última rodada. | MB p.5, p.11 | CONFIRMADA |

## 7. Motores e aproximação

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-ENG-01 | Há um espaço de Motor azul e um laranja. Ambos são obrigatórios. | MB p.5, p.6 | CONFIRMADA |
| R-ENG-02 | **Assim que o segundo dado é colocado**, a soma dos dois dados é a Velocidade. | MB p.6 | CONFIRMADA |
| R-ENG-03 | Velocidade menor que o marcador azul: o avião não avança. Entre os dois marcadores: avança 1 espaço. Maior que o marcador laranja: avança 2. Como os marcadores ficam *entre* números, não há empate. Exemplos do manual: com azul em 4/5 e laranja em 8/9, soma 4 avança 0, soma 7 avança 1 e soma 10 avança 2. | MB p.6 | CONFIRMADA |
| R-ENG-04 | Na rodada final, a velocidade é comparada com os Freios em vez de com os marcadores de aerodinâmica, e o avião não avança. | MB p.10 | CONFIRMADA |
| R-ENG-05 | Escala do medidor de velocidade: de 2 a 12. | MB p.6, p.7 (ilustração) | ILUSTRAÇÃO |
| R-APP-01 | A pista de aproximação é uma sequência de espaços terminando no Aeroporto. A "Posição Atual" é o espaço visível na tela do painel. | MB p.3, p.6 | CONFIRMADA |
| R-APP-02 | Colisão: se houver tokens de Avião na Posição Atual e o avião tiver que avançar, a partida é perdida. | MB p.6 | CONFIRMADA |
| R-APP-03 | Tokens de Avião que **chegam** ao espaço da Posição Atual não causam colisão. | MB p.6 | CONFIRMADA |
| R-APP-04 | Avanço de 2 espaços: cada passo verifica a colisão a partir da posição em que o avião está naquele passo. Se o 1º passo leva a um espaço com tráfego, o 2º passo causa colisão. | MB p.6 | INFERIDA da regra de colisão aplicada a cada passo. Ver P7. |
| R-APP-05 | Ultrapassar: se o Aeroporto está na Posição Atual e o avião tem que avançar, a partida é perdida. | MB p.6 | CONFIRMADA |
| R-APP-06 | Chegada antecipada: com o Aeroporto na Posição Atual antes da última rodada, o avião fica "em espera". Os jogadores devem jogar as rodadas seguintes sem avançar, ou seja, com velocidade abaixo do marcador azul. | MB p.10 | CONFIRMADA |
| R-APP-07 | As pistas de aproximação têm tamanhos diferentes conforme o cenário. | RV p.2 | CONFIRMADA |

## 8. Rádio

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-RAD-01 | O Piloto tem 1 espaço de Rádio e o Copiloto tem 2. | MB p.7 | CONFIRMADA |
| R-RAD-02 | Conta-se o valor do dado em espaços começando pela Posição Atual (1 = Posição Atual). Remove-se **imediatamente** um token de Avião desse espaço. | MB p.7 | CONFIRMADA |
| R-RAD-03 | Sem efeito se não houver Avião no espaço indicado. A colocação continua sendo legal. | MB p.7 | CONFIRMADA |
| R-RAD-04 | Se o valor ultrapassar o fim da pista (aponta além do Aeroporto), não há efeito. | | INFERIDA: não existe espaço além do aeroporto, então vale R-RAD-03. Ver P8. |

## 9. Trem de pouso (somente Piloto)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-GEA-01 | São 3 espaços, com restrições **1/2**, **3/4** e **5/6**. | MB p.7 (ilustração), p.4 | ILUSTRAÇÃO, consistente com o exemplo do texto ("4 no espaço 3/4") |
| R-GEA-02 | A ordem de acionamento **não** importa. | MB p.7 | CONFIRMADA |
| R-GEA-03 | Ao colocar o dado, desliza-se o interruptor (luz verde) e avança-se **imediatamente** o marcador azul de aerodinâmica 1 espaço. | MB p.7 | CONFIRMADA |
| R-GEA-04 | Com os 3 acionados, o marcador azul fica entre 7 e 8. | MB p.7 | CONFIRMADA |
| R-GEA-05 | Jogar num espaço cujo interruptor já está verde **é permitido** e não tem efeito. | MB p.7 | CONFIRMADA |
| R-GEA-06 | Condição de vitória B: os 3 interruptores do trem estão verdes. | MB p.7, p.11 | CONFIRMADA |

## 10. Flaps (somente Copiloto)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-FLA-01 | São 4 espaços, com restrições **1/2**, **2/3**, **4/5** e **5/6**. | MB p.4, p.8 (ilustração) | ILUSTRAÇÃO, consistente com o texto ("só pode colocar 1 ou 2 no primeiro espaço"; "2 no segundo espaço (2/3)") |
| R-FLA-02 | Devem ser acionados **em ordem, de cima para baixo**. | MB p.8 | CONFIRMADA |
| R-FLA-03 | Ao acionar, desliza-se o interruptor e avança-se **imediatamente** o marcador laranja 1 espaço. | MB p.8 | CONFIRMADA |
| R-FLA-04 | Com os 4 acionados, o marcador laranja passa do 12. | MB p.8 | CONFIRMADA |
| R-FLA-05 | Dado em espaço de Flap já acionado: o manual dos Flaps não diz. Pela analogia com o trem (R-GEA-05), seria permitido e sem efeito. | | AMBÍGUA (P9) |
| R-FLA-06 | Condição de vitória B: os 4 interruptores dos Flaps estão verdes. | MB p.8, p.11 | CONFIRMADA |

## 11. Freios (somente Piloto)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-BRK-01 | São 3 espaços, que exigem os valores exatos **2**, **4** e **6**. | MB p.4 (D), p.9 | CONFIRMADA |
| R-BRK-02 | Devem ser acionados em ordem: 2, depois 4, depois 6. | MB p.9 | CONFIRMADA |
| R-BRK-03 | Ao acionar, avança-se **imediatamente** o marcador vermelho 1 casa. | MB p.9 | CONFIRMADA |
| R-BRK-04 | Os freios só importam na rodada final. Não é obrigatório acionar todos. | MB p.9, p.10 | CONFIRMADA |
| R-BRK-05 | Posições do marcador: começa à esquerda do 2. O exemplo diz que, com o segundo freio acionado, o marcador fica "entre 4 e 5". A posição após o 1º freio não é dita: pela ilustração, entre 2 e 3. Após o 3º freio, além do 6. | MB p.9, p.10 | Parte CONFIRMADA, parte ILUSTRAÇÃO (P10) |
| R-BRK-06 | O marcador "não pode estar abaixo de 2". Sem nenhum freio acionado, não é possível parar o avião. | MB p.10 | CONFIRMADA. Equivale a perder por R-LND-04, já que a velocidade mínima é 2. |
| R-BRK-07 | Condição de vitória D: Velocidade menor que a posição do marcador de freio. A comparação é feita **no momento em que o 2º dado do Motor é colocado**, com o marcador de freio daquele momento ("when playing the second engine die... compare it WITH YOUR BRAKES"; "Your Speed is less than your Brakes when you placed your Engine dice"). Um freio acionado depois disso, na rodada final, não conta para D. | MB p.10, p.11 | CONFIRMADA (inglês) |

## 12. Concentração e Café

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-COF-01 | São 3 espaços de Concentração. Os dois jogadores podem colocar qualquer dado. | MB p.8, p.4 (F) | CONFIRMADA |
| R-COF-02 | Ao colocar um dado ali, ganha-se **imediatamente** um token de Café. O máximo é 3. | MB p.8 | CONFIRMADA |
| R-COF-03 | Ao colocar um dado em **qualquer** espaço, o jogador pode gastar 1 ou mais tokens para modificar esse dado. Cada token soma ou subtrai 1. | MB p.8 | CONFIRMADA |
| R-COF-04 | Qualquer jogador usa os tokens, independentemente de quem os criou. | MB p.8 | CONFIRMADA |
| R-COF-05 | Tokens não gastos permanecem para a rodada seguinte. | MB p.8 | CONFIRMADA |
| R-COF-06 | O valor modificado fica entre 1 e 6, sem dar a volta (1−1 não vira 6 e 6+1 não vira 1). | MB p.8 | CONFIRMADA |
| R-COF-07 | Com o máximo de 3 tokens, ainda é permitido colocar um dado na Concentração (sem ganhar token). | | AMBÍGUA (P4) |
| R-COF-08 | Um dado colocado na Concentração pode ser modificado por café? O texto diz "qualquer lugar", e não haveria efeito prático. | MB p.8 | INFERIDA: é permitido e irrelevante. |

## 13. Fase 3: fim da rodada e altitude

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-END-01 | Passos em ordem: (1) avançar a Trilha de Altitude 1 espaço (−1000 pés); (2) recolher os dados; (3) verificar o fim de jogo. | MB p.9 | CONFIRMADA |
| R-END-02 | Se o Aeroporto está na Posição Atual e o Avião aparece na Altitude Atual, joga-se a rodada final. Caso contrário, começa uma nova rodada. | MB p.9, p.10 | CONFIRMADA |
| R-END-03 | Se o Avião aparece na Altitude Atual e o Aeroporto não está na Posição Atual, houve pouso forçado antes do aeroporto e a partida é perdida. | MB p.10 | CONFIRMADA |
| R-ALT-01 | A trilha base tem 7 espaços, um por rodada: 6000, 5000, 4000, 3000, 2000, 1000 e o espaço do Avião (rodada final). | MB p.9, p.3 (ilustração) | 7 espaços CONFIRMADOS. Os valores intermediários são ILUSTRAÇÃO. |
| R-ALT-02 | Existe mais de uma trilha de altitude: a do jogo base é "verde/amarelo". Cenários vermelhos e pretos podem usar outra. | MB p.3 (5) | CONFIRMADA a existência. Conteúdo: FALTA COMPONENTE (P12). |
| R-END-04 | Os módulos podem acrescentar passos ao fim da rodada. O Querosene, por exemplo, acrescenta um passo "bem no final". | RV p.3 | CONFIRMADA |

## 14. Rodada final e pouso

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-LND-00 | A rodada final começa quando o Aeroporto está na Posição Atual e o Avião está na Altitude Atual. Ela é jogada normalmente (fases 1 e 2), com os Motores comparados aos Freios. | MB p.10 | CONFIRMADA |
| R-LND-01 | **A**: não há tokens de Avião na Pista de Aproximação. | MB p.7, p.11 | CONFIRMADA |
| R-LND-02 | **B**: todos os interruptores de Flaps e de Trem de Pouso estão verdes. | MB p.11 | CONFIRMADA |
| R-LND-03 | **C**: o eixo está completamente horizontal. | MB p.11 | CONFIRMADA |
| R-LND-04 | **D**: a Velocidade era menor que os Freios no momento em que os dados do Motor foram colocados. O resultado é registrado ao resolver o Motor e avaliado no fim da rodada, junto com A–C (ver R-BRK-07). | MB p.10, p.11 | CONFIRMADA (inglês) |
| R-LND-05 | As condições são avaliadas **ao final** da rodada final. Se todas valem, vitória. | MB p.11 | CONFIRMADA |
| R-LND-06 | Se alguma condição falha, a partida é perdida. | MB p.11 ("Você ganha se...") | INFERIDA: o manual só define a vitória, e não existe outro desfecho possível no fim da rodada final. |
| R-LND-07 | As regras obrigatórias (R-MAND) continuam valendo na rodada final. | MB p.5 ("a cada rodada") | INFERIDA |
| R-LND-08 | Os módulos acrescentam condições: o Estágio exige o treinamento completo e os Freios de Gelo exigem o marcador além do 5. | RV p.4, p.5 | CONFIRMADA |

## 15. Condições de derrota (consolidadas)

| Id | Condição | Momento | Fonte | Status |
|---|---|---|---|---|
| R-LOSS-01 | Eixo atinge ou passa por um X. | Imediato, ao resolver o Eixo | MB p.5 | CONFIRMADA |
| R-LOSS-02 | Colisão: há tráfego na Posição Atual e o avião precisa avançar. | Imediato, ao resolver os Motores | MB p.6 | CONFIRMADA |
| R-LOSS-03 | Ultrapassagem: o Aeroporto está na Posição Atual e o avião precisa avançar. | Imediato, ao resolver os Motores | MB p.6 | CONFIRMADA |
| R-LOSS-04 | Falta dado obrigatório no Eixo ou nos Motores. | Fim da rodada | MB p.5 | CONFIRMADA |
| R-LOSS-05 | Altitude acabou sem chegar ao aeroporto. | Fim da rodada | MB p.10 | CONFIRMADA |
| R-LOSS-06 | Falha em qualquer condição de pouso A a D. | Fim da rodada final | MB p.11 | INFERIDA (R-LND-06) |
| R-LOSS-07 | Querosene atinge o espaço X. | Imediato, inclusive na rodada final | RV p.3 | CONFIRMADA |
| R-LOSS-08 | Estagiário não treinado: ainda há fichas na placa no final do jogo. | Fim do jogo | RV p.4 | CONFIRMADA |
| R-LOSS-09 | Tempo Real: o tempo acaba com o Eixo ou os Motores incompletos. | Ao acabar o tempo | RV p.5 | CONFIRMADA |
| R-LOSS-10 | Freios de Gelo: o marcador não chegou além do 5 até o fim do jogo. | Fim do jogo | RV p.5 | CONFIRMADA |
| R-LOSS-11 | Curvas: o eixo está fora das posições permitidas num espaço pelo qual o avião passa ao avançar. | Imediato, ao avançar | RV p.3 | CONFIRMADA |

---

## 16. Aeroportos

Lidos dos cards de cenário (RV p.6–8). A pista de cada aeroporto é um componente físico ainda não fornecido.

| Código | Nome | Cenários (cores) |
|---|---|---|
| YUL | Montréal-Trudeau | verde (tutorial do MB) |
| LHR | Heathrow | verde, amarelo |
| HND | Haneda (Tóquio) | verde, vermelho |
| OSL | Gardermoen | verde, vermelho |
| ATL | Hartsfield-Jackson | verde, amarelo |
| PRG | Václav Havel | verde, amarelo |
| TGU | Toncontín | amarelo, vermelho |
| GIG | Galeão | amarelo, vermelho |
| KEF | Keflavík | amarelo, preto |
| KUL | Kuala Lumpur | amarelo, preto |
| PBH | Paro | vermelho, preto |

São 11 aeroportos, com códigos confirmados no Flight Log em inglês (incluindo HND, que a tradução PT omitia).

## 17. Dificuldades

| Cor | Nome no RV | Fonte |
|---|---|---|
| Verde | Pouso de rotina | RV p.2 |
| Amarelo | Condições excepcionais | RV p.2 |
| Vermelho | Apenas pilotos de elite | RV p.2 |
| Preto | Heroic Landing (pouso heroico) | RV p.2 |

## 18. Cenários (21)

O RV p.2 fala em "21 disponíveis nas páginas 6, 7 e 8", e a contagem abaixo fecha em 21.

Ids propostos: `<código>_<cor>`. Os módulos e as habilidades vêm dos ícones de cada card. A pista de aproximação de
cada cenário é a "correspondente ao nome e à cor do cenário" (RV p.2) e ainda não foi fornecida (P12).

| Id | Aeroporto | Cor | Módulos (ícones) | Habilidades | Fonte | Observação |
|---|---|---|---|---|---|---|
| `YUL_green` | YUL | verde | — | 0 | MB, RV p.6 | Tutorial; tudo descrito no MB |
| `LHR_green` | LHR | verde | — | 0 | RV p.6 | "há tráfego no final da sua abordagem" |
| `HND_green` | HND | verde | — | 0 | RV p.6 | "curva ampla à esquerda", que sugere Curvas na pista |
| `OSL_green` | OSL | verde | Querosene | 0 | RV p.6 | |
| `ATL_green` | ATL | verde | Estágio | 0 | RV p.6 | "céu repleto de trânsito" |
| `PRG_green` | PRG | verde | Querosene | 2 | RV p.6 | |
| `LHR_yellow` | LHR | amarelo | Estágio | 0 | RV p.7 | "padrões de espera" |
| `TGU_yellow` | TGU | amarelo | Querosene | 2 | RV p.7 | "curva final bem fechada" |
| `GIG_yellow` | GIG | amarelo | Vento | 1 | RV p.7 | |
| `KEF_yellow` | KEF | amarelo | Freios de Gelo | 1 | RV p.7 | |
| `PRG_yellow` | PRG | amarelo | Vazamento de Querosene | 2 | RV p.7 | |
| `KUL_yellow` | KUL | amarelo | Querosene | 1 | RV p.7 | |
| `ATL_yellow` | ATL | amarelo | Vazamento de Querosene | 1 | RV p.7 | |
| `PBH_red` | PBH | vermelho | Querosene, Tempo Real | 2 | RV p.8 | |
| `HND_red` | HND | vermelho | Estágio | 1 | RV p.8 | |
| `GIG_red` | GIG | vermelho | Vento, Vazamento de Querosene | 2 | RV p.8 | |
| `OSL_red` | OSL | vermelho | Vazamento de Querosene, Freios de Gelo | 2 | RV p.8 | |
| `TGU_red` | TGU | vermelho | Querosene, Vento | 2 | RV p.8 | |
| `KEF_black` | KEF | preto | Vento, Freios de Gelo | 2 | RV p.8 | |
| `KUL_black` | KUL | preto | Querosene, Tempo Real | 2 | RV p.8 | |
| `PBH_black` | PBH | preto | Querosene, Tempo Real | 2 | RV p.8 | |

As cores de PBH, KUL e KEF na p.8 foram lidas do cabeçalho do card: PBH vermelho no topo, KEF, KUL e PBH pretos
embaixo. Total: 6 verdes, 7 amarelos, 5 vermelhos e 3 pretos.

Os efeitos de pista (Tráfego e Curvas) **não** aparecem nos cards. Eles estão impressos nas pistas de aproximação (RV p.3).

## 19. Efeitos da pista de aproximação

### Tráfego (dado de Tráfego)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-TRD-01 | No **início da rodada**, se a Posição Atual tem ícone(s) de Tráfego, rola-se o dado de Tráfego uma vez por ícone. | RV p.3 | CONFIRMADA |
| R-TRD-02 | Cada rolagem adiciona um token de Avião ao espaço indicado pelo valor, contando a partir da Posição Atual (1 = Posição Atual). | RV p.3 (exemplo: 3 vai para o 3º espaço) | CONFIRMADA |
| R-TRD-03 | Se o valor é maior que o número de espaços restantes, o Avião vai para o último espaço (o Aeroporto). | RV p.3 | CONFIRMADA |
| R-TRD-04 | Sem token de Avião no estoque (12 no total), nenhum é colocado. | RV p.3, MB p.3 | CONFIRMADA |
| R-TRD-05 | Ícones de espaços pelos quais o avião passou ao avançar 2 não são rolados. | RV p.3 | CONFIRMADA |
| R-TRD-06 | Se o avião permanece num espaço com ícone por mais de uma rodada, rola-se a cada rodada. | RV p.3 | CONFIRMADA |
| R-TRD-07 | Faces do dado de Tráfego: o RV mostra um dado preto com "3", mas não descreve as faces. | | FALTA COMPONENTE (P14) |

### Curvas

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-TRN-01 | Ao avançar na Pista de Aproximação, se o Eixo não está numa das posições permitidas impressas na Posição Atual, a partida é perdida. | RV p.3 | CONFIRMADA |
| R-TRN-02 | Ao avançar 2, a restrição vale para os dois espaços percorridos. | RV p.3 | CONFIRMADA |
| R-TRN-03 | Avançando 0, não há restrição. | RV p.3 | CONFIRMADA |
| R-TRN-04 | Qual espaço é verificado: o de saída (a Posição Atual antes do avanço) ou o de chegada? "Na tela Posição Atual" junto com "ambos os espaços pelos quais você voa" sugere os espaços **de saída** de cada passo. | RV p.3 | AMBÍGUA (P15) |
| R-TRN-05 | Posições permitidas por espaço. | | FALTA COMPONENTE |

## 20. Módulos (6)

### Querosene (`kerosene`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-KER-01 | A trilha de Querosene fica à esquerda do painel, com o marcador em 20. | RV p.3 | CONFIRMADA |
| R-KER-02 | Ação: Piloto **ou** Copiloto coloca um dado de qualquer valor no espaço de Querosene e desce imediatamente o marcador tantos espaços quanto o valor. | RV p.3 | CONFIRMADA |
| R-KER-03 | Bem no final da fase de Fim da Rodada: se ninguém colocou dado no espaço, perdem-se 6 de querosene. | RV p.3 | CONFIRMADA |
| R-KER-04 | A qualquer momento, inclusive na rodada final, se o marcador atingir o espaço X, a partida é perdida. | RV p.3 | CONFIRMADA |
| R-KER-05 | Posição do X na trilha (abaixo do 1? em 0?). | | FALTA COMPONENTE (P16) |
| R-KER-06 | O espaço de Querosene é um único espaço por rodada (ocupado por um dado). | RV p.3 | INFERIDA da ilustração e do "se você não colocou um dado aqui" |

### Estágio (`intern`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-INT-01 | A Placa do Estagiário fica abaixo do painel. Uma ficha aleatória de Estagiário vai virada para cima em cada espaço. | RV p.4 | CONFIRMADA |
| R-INT-02 | Na sua vez, o jogador pode colocar um dado de qualquer valor no espaço da sua cor da placa e pegar a primeira ficha disponível mais próxima do seu lado. | RV p.4 | CONFIRMADA |
| R-INT-03 | A ficha pode ser colocada em qualquer espaço onde o jogador normalmente colocaria um dado. Ela resolve o efeito como se fosse um dado com o número da ficha. | RV p.4 | CONFIRMADA |
| R-INT-04 | A ficha não pode ser modificada por Café. | RV p.4 | CONFIRMADA |
| R-INT-05 | A ficha não pode ir para a Concentração. | RV p.4 | CONFIRMADA |
| R-INT-06 | O dado colocado na placa tem que ter valor **diferente** da próxima ficha disponível. | RV p.4 | CONFIRMADA |
| R-INT-07 | Se ainda houver fichas na placa no final do jogo, a partida é perdida. | RV p.4 | CONFIRMADA |
| R-INT-08 | A placa tem um espaço de dado azul na ponta esquerda, 5 espaços de ficha e um espaço de dado laranja na ponta direita. "Mais próxima do seu lado": o Piloto pega da esquerda e o Copiloto da direita. A ilustração mostra as fichas 6, 4, 3, 5 e 1. | RV p.4 | ILUSTRAÇÃO |
| R-INT-09 | Conjunto total de fichas de Estagiário na caixa (valores e quantidade), de onde saem as 5 aleatórias. | | FALTA COMPONENTE (P17) |
| R-INT-10 | Colocar a ficha é imediato (no mesmo turno) ou ocupa a próxima jogada? | RV p.4 ("You can then place that token") | AMBÍGUA (P17b) |
| R-INT-11 | O espaço de dado da placa pode ser usado mais de uma vez por rodada? Ele é um espaço como os outros, então fica ocupado até o fim da rodada. | RV p.4 | INFERIDA |

### Vento (`wind`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-WND-01 | A ficha azul de Avião fica no Anel de Vento, à direita do painel, com o nariz apontando para o espaço central branco. | RV p.4 | CONFIRMADA |
| R-WND-02 | Imediatamente após a fase do Eixo, a ficha gira tantos espaços quanto a posição atual do Eixo fora do centro, na direção da inclinação, mesmo que o Eixo não tenha se movido. Inclinação para o Piloto gira a ficha para a esquerda. | RV p.4 (exemplo) | CONFIRMADA |
| R-WND-03 | Na fase do Motor, soma-se à velocidade o valor do espaço para onde a ficha aponta. Vale em todas as rodadas, inclusive na final. | RV p.4 | CONFIRMADA |
| R-WND-04 | Valores do anel (o exemplo mostra +2) e o que acontece no fim do anel. | | FALTA COMPONENTE (P18) |
| R-WND-05 | A "fase do Eixo" é o momento em que o 2º dado do Eixo é resolvido. Se o Motor for resolvido antes do Eixo na rodada, o Vento usa a posição da ficha nesse momento. | | INFERIDA, mas precisa de confirmação (P18) |

### Tempo Real (`real_time`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-RTM-01 | No início de cada rodada, um cronômetro de 60 s é iniciado imediatamente após a rolagem dos dados. | RV p.5 | CONFIRMADA |
| R-RTM-02 | Quando o tempo acaba, nenhum dado pode mais ser colocado e a rodada termina imediatamente. Os dados não colocados são ignorados. | RV p.5 | CONFIRMADA |
| R-RTM-03 | Se o Eixo ou os Motores não estiverem preenchidos nesse momento, a partida é perdida. | RV p.5 | CONFIRMADA |

### Vazamento de Querosene (`kerosene_leak`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-KLK-01 | A trilha de Querosene é configurada normalmente. Uma ficha de Estagiário virada para baixo fica sobre o espaço do dado, para lembrar que ele não pode ser usado. | RV p.5 | CONFIRMADA |
| R-KLK-02 | A Ação Querosene deixa de existir, e não se perdem mais 6 no fim da rodada. | RV p.5 | CONFIRMADA |
| R-KLK-03 | Em vez disso, a perda de querosene é igual à diferença entre os dois dados do Motor, mais 1. Exemplo: 6 e 3 dão 4. | RV p.5 | CONFIRMADA. O momento (ao resolver o Motor) é INFERIDO. |
| R-KLK-04 | O X continua causando derrota (R-KER-04). | RV p.5 ("configure normalmente") | INFERIDA |

### Freios de Gelo (`ice_brakes`)

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-ICE-01 | A placa de Freios de Gelo cobre os freios originais. Ela tem 4 espaços em cima (2, 3, 4 e 5), 4 espaços embaixo (2, 3, 4 e 5) e a pista do marcador no meio. Pela ilustração, a fileira de cima é azul e a de baixo é laranja e azul. | RV p.5 | CONFIRMADA. As cores dos espaços vêm da ILUSTRAÇÃO (P19). |
| R-ICE-02 | Funciona como os freios normais, mas exige 2 dados de mesmo valor, um em cima e um embaixo, **na mesma rodada**. | RV p.5 | CONFIRMADA |
| R-ICE-03 | Se um dado foi colocado num espaço e o espaço oposto não foi preenchido na mesma rodada, ele é perdido: retira-se o dado no final da rodada sem mover o marcador. | RV p.5 | CONFIRMADA |
| R-ICE-04 | Não há interruptores. Os espaços são usados em ordem, da esquerda para a direita. | RV p.5 | CONFIRMADA |
| R-ICE-05 | Não se pode jogar num espaço à esquerda do marcador, isto é, onde já houve dados numa rodada anterior. | RV p.5 | CONFIRMADA |
| R-ICE-06 | O marcador pode avançar mais de uma vez na mesma rodada. | RV p.5 | CONFIRMADA |
| R-ICE-07 | O marcador tem que passar além do 5 antes do fim do jogo. Caso contrário, a partida é perdida. | RV p.5 | CONFIRMADA |
| R-ICE-08 | No final da última rodada, a velocidade deve ser menor que o marcador de freio. | RV p.5 | CONFIRMADA |
| R-ICE-09 | Os valores dos dados precisam coincidir com o número do espaço (2 a 5)? A ilustração mostra 2/2 no primeiro par. | RV p.5 | ILUSTRAÇÃO, provável (P19) |

## 21. Habilidades especiais

| Id | Regra | Fonte | Status |
|---|---|---|---|
| R-ABL-01 | Alguns cenários oferecem cartas de Habilidade Especial. O número de estrelas no card indica quantas cartas usar (1 ou 2). | RV p.2 | CONFIRMADA |
| R-ABL-02 | Cada carta oferece uma habilidade diferente. Os jogadores escolhem quais usar ("experimente... escolha aquelas que melhor o ajudarão"). | RV p.2 | CONFIRMADA |
| R-ABL-03 | **Mastery** (Domínio): "If you play 2 dice with the same value on the ENGINES, immediately gain a Reroll token (only if a Reroll token is available)." | RV p.2 (carta reproduzida) | CONFIRMADA. "Available" é AMBÍGUO (P23). |
| R-ABL-04 | **Synchronisation** (Sincronização): "If you have placed at least one die on Landing Gear and one die on Flaps, immediately roll the Traffic die. Place it on any empty space on the Control Panel regardless of its colour. Apply the effect of the Traffic die as if it were a normal die. It counts as an extra action for this turn." | RV p.2 (carta reproduzida) | CONFIRMADA. Escopo e uso são AMBÍGUOS (P24). |
| R-ABL-06 | Demais cartas de habilidade: nomes, textos e quantidade. | | FALTA COMPONENTE (P20) |
| R-ABL-05 | Quem escolhe as cartas e quando (antes da partida?). | RV p.2 | AMBÍGUA (P20) |

---

## 22. Regras compartilhadas e específicas

**Compartilhadas** (núcleo, todo cenário): seções 1 a 15. Ficam em `core/` e `mechanics/`.

**Específicas por cenário**, todas como dados:
- pista de aproximação: tamanho, tráfego inicial, ícones de Tráfego e posições permitidas de Curva por espaço;
- trilha de altitude: espaços, rerrolagens e seta de primeiro jogador;
- lista de módulos;
- número de habilidades.

**Plugins**: 6 módulos (`kerosene`, `intern`, `wind`, `real_time`, `kerosene_leak`, `ice_brakes`), 2 efeitos de pista
(`traffic_dice` e `turns`, ativados pelos dados da pista e não pelo card) e as cartas de habilidade.
