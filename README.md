# AI-SkyTeam

Implementação digital, determinística e orientada a dados das regras do board game **Sky Team**, em Python,
servindo tanto para jogar por interface gráfica quanto como ambiente de treino de agentes de IA.

A engine de regras é independente da interface e só usa a biblioteca padrão. Nenhum asset comercial do jogo é reproduzido.

## Estado atual

- **Etapa 1** (regras): conferida com os manuais oficiais em inglês.
- **Etapas 2 a 5** (arquitetura, core, mecânicas, vitória e derrota): implementadas para o jogo base e testadas.
- **Etapa 6**: YUL Montréal-Trudeau jogável de ponta a ponta.
- **Etapas 10 e 11**: ambiente de IA (ações, máscara, observação vetorial, recompensa), replay e simulador headless.
- **IA**: modelo treinado por autojogo em `models/yul_ppo.pt`, pousa em 82% das partidas do YUL.
- **Pendente**: as demais pistas de aproximação, módulos, habilidades e interface.

## Jogar a dois (terminal)

Precisa de Python 3.11 ou mais novo; não há outras dependências.

```bash
git clone https://github.com/JrCrespi/AI-SkyTeam.git
cd AI-SkyTeam
python -m skyteam.play
```

Os dois jogadores dividem o mesmo computador. Quando a vez passa, a tela é limpa e o jogo espera Enter,
para que ninguém veja os dados do parceiro. Digite o número da opção; `h` mostra o histórico, `v` volta e
`q` sai. `--seed N` repete uma partida.

## HUD gráfico provisório

Tela de teste em Pygame, com visual próprio (não é a interface final da Etapa 12).

```bash
python -m pip install pygame
python -m skyteam.ui.hud
```

Clique num dos seus dados e depois num espaço destacado: verde é jogada legal, amarelo só é legal gastando
café (ajuste com os botões − e +). Quando a vez passa, a tela é coberta até o próximo jogador clicar em
"Mostrar meus dados". `N` começa um novo jogo e `Esc` sai.

## IA

```bash
python -m pip install -e ".[train]"      # torch e numpy

# ver o modelo treinado jogar 1000 partidas
python -m skyteam.simulate --scenario YUL_green --policy models/yul_ppo.pt --games 1000

# continuar melhorando por autojogo
python -m skyteam.ai.ppo --init models/yul_ppo.pt --steps 12000000 --config-bonus 0.2 --out runs/treino

# aprender com as partidas gravadas em games/ e depois seguir por autojogo
python -m skyteam.ai.imitation --data games --init models/yul_ppo.pt --out runs/bc.pt
python -m skyteam.ai.ppo --init runs/bc.pt --out runs/treino2
```

Detalhes e resultados em [Ambiente de IA](docs/ai_environment.md#treinamento-da-ia).

## Uso como biblioteca

```python
from skyteam.core.game import SkyTeamGame
from skyteam.scenarios.loader import load_scenario

game = SkyTeamGame(load_scenario("YUL_green"))
game.reset(seed=42)
player = game.current_player
actions = game.get_legal_actions(player)
result = game.step(actions[0])
print("\n".join(game.history()))
```

Cenários disponíveis: `YUL_green` (Montréal, tutorial). Os demais entram conforme as pistas forem transcritas.

Simulação sem interface:

```bash
python -m skyteam.simulate --scenario YUL_green --games 10000 --seed 0
```

## Testes

```bash
python -m pip install pytest
python -m pytest
```

## Documentação

- [Análise técnica](docs/00_analise_tecnica.md)
- [Arquitetura](docs/architecture.md)
- [Registro de regras](docs/etapa1/regras_extraidas.md) e [pendências](docs/etapa1/pendencias_regras.md)
- [Mapeamento regra → código](docs/rules_mapping.md)
- [Ambiente de IA e simulador](docs/ai_environment.md)
- [Matriz de cobertura](docs/rules_coverage_matrix.md)
