# AI-SkyTeam

Implementação digital, determinística e orientada a dados das regras do board game **Sky Team**, em Python,
servindo tanto para jogar por interface gráfica quanto como ambiente de treino de agentes de IA.

A engine de regras é independente da interface e só usa a biblioteca padrão. Nenhum asset comercial do jogo é reproduzido.

## Estado atual

- **Etapa 1** (regras): conferida com os manuais oficiais em inglês.
- **Etapas 2 a 5** (arquitetura, core, mecânicas, vitória e derrota): implementadas para o jogo base e testadas.
- **Etapa 6**: YUL Montréal-Trudeau jogável de ponta a ponta.
- **Pendente**: as demais pistas de aproximação, módulos, habilidades, API de IA, simulador e interface.

## Uso

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
- [Matriz de cobertura](docs/rules_coverage_matrix.md)
