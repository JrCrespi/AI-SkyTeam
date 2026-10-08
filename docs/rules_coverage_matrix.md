# Matriz de cobertura das regras

Atualizada ao fim de cada etapa. Situação atual: **Etapas 2 a 6, 10 e 11 concluídas para o jogo base e YUL** (586 testes verdes). Módulos, habilidades e cenários oficiais vêm nas próximas etapas.

Os testes de ponta a ponta usam uma pista **sintética** (`tests/fixtures`), porque as pistas oficiais ainda não foram transcritas.

"Fonte" indica a situação da regra no registro (`docs/etapa1/regras_extraidas.md`):
**Manual** (confirmada no texto), **Parcial** (há itens de ilustração, inferidos ou ambíguos) ou **Falta componente**.

| Regra/Mecânica | Ids | Fonte | Implementada | Testada | Arquivo | Teste |
|---|---|---|---|---|---|---|
| Preparação | R-SET-* | Manual | Sim | Sim | core/game.py | test_data.py |
| Fases e comunicação | R-GEN-04, R-COM-* | Manual | Sim | Sim | core/game.py, core/rules.py | test_phases.py |
| Turnos e colocação | R-TURN-* | Parcial (P2) | Sim | Sim | core/rules.py | test_phases.py, test_invariants.py |
| Ações obrigatórias | R-MAND-* | Manual | Sim | Sim | mechanics/loss.py | test_loss_conditions.py |
| Dados | R-DIE-* | Manual | Sim | Sim | core/rng.py, core/game.py | test_rng.py |
| Rerrolagem | R-RER-* | Parcial (P3) | Sim | Sim | mechanics/rerolls.py | test_rerolls.py |
| Eixo | R-AXI-* | Parcial (P21) | Sim | Sim | mechanics/axis.py | test_axis.py |
| Motores | R-ENG-* | Manual | Sim | Sim | mechanics/engines.py | test_engines.py |
| Aproximação | R-APP-* | Parcial (P7, P12) | Sim | Sim | mechanics/approach.py | test_approach.py |
| Rádio | R-RAD-* | Manual | Sim | Sim | mechanics/radio.py | test_radio.py |
| Trem de pouso | R-GEA-* | Manual (valores por ilustração) | Sim | Sim | mechanics/landing_gear.py | test_landing_gear.py |
| Flaps | R-FLA-* | Parcial (P9) | Sim | Sim | mechanics/flaps.py | test_flaps.py |
| Freios | R-BRK-* | Parcial (P10) | Sim | Sim | mechanics/brakes.py | test_brakes.py |
| Concentração / Café | R-COF-* | Parcial (P4) | Sim | Sim | mechanics/concentration.py | test_concentration.py |
| Fim de rodada / Altitude | R-END-*, R-ALT-* | Parcial (verde/amarela OK; vermelha/preta: P12b) | Sim | Sim | core/game.py, mechanics/altitude.py | test_loss_conditions.py |
| Pouso (vitória A–D) | R-LND-* | Manual | Sim | Sim | mechanics/landing.py | test_landing.py |
| Derrotas do jogo base (R-LOSS-01..06) | R-LOSS-01..06 | Manual | Sim | Sim | mechanics/loss.py, axis.py, approach.py, landing.py | test_loss_conditions.py, test_axis.py, test_approach.py, test_landing.py |
| Derrotas de módulos (R-LOSS-07..11) | R-LOSS-07..11 | Manual | Não | Não | modules/ | — |
| Efeito de pista: dado de Tráfego | R-TRD-* | Parcial (P14) | Não | Não | modules/traffic_dice.py | test_traffic_dice.py |
| Efeito de pista: Curvas | R-TRN-* | Parcial (P15) | Não | Não | modules/turns.py | test_turns.py |
| Módulo Querosene | R-KER-* | Parcial (P16) | Não | Não | modules/kerosene.py | test_kerosene.py |
| Módulo Estágio | R-INT-* | Parcial (P17) | Não | Não | modules/intern.py | test_intern.py |
| Módulo Vento | R-WND-* | Falta componente (P18) | Não | Não | modules/wind.py | test_wind.py |
| Módulo Tempo Real | R-RTM-* | Manual (P22 é decisão de projeto) | Não | Não | modules/real_time.py | test_real_time.py |
| Módulo Vazamento de Querosene | R-KLK-* | Manual | Não | Não | modules/kerosene_leak.py | test_kerosene_leak.py |
| Módulo Freios de Gelo | R-ICE-* | Parcial (P10b, P19) | Não | Não | modules/ice_brakes.py | test_ice_brakes.py |
| Habilidade Mastery | R-ABL-03 | Parcial (P23) | Não | Não | abilities/mastery.py | test_abilities.py |
| Habilidade Synchronisation | R-ABL-04 | Parcial (P24) | Não | Não | abilities/synchronisation.py | test_abilities.py |
| Demais habilidades | R-ABL-06 | Falta componente (P20) | Não | Não | abilities/ | test_abilities.py |
| Cenário YUL_green (Etapa 6) | seção 18 | Manual + pista transcrita pelo João | Sim | Sim | data/scenarios/YUL_green.json | test_scenario_yul.py |
| Demais cenários (20) | seção 18 | Parcial (pistas: P12) | Não | Não | data/scenarios/ | test_scenarios.py |
| Aeroportos (11) | seção 16 | Manual | Não | Não | data/airports/ | test_scenarios.py |
| Informação oculta | R-GEN-03 | Manual | Sim | Sim | core/visibility.py | test_visibility.py |
| Serialização, clone, undo, replay por ações | — | — | Sim | Sim | core/state.py, core/game.py | test_serialization.py |
| Invariantes | — | — | Sim | Sim | core/validation.py | test_invariants.py |
| Espaço de ações, máscara, observação vetorial (Etapa 10) | — | — | Sim | Sim | ai/action_space.py, ai/action_mask.py, ai/observation.py | test_ai.py |
| Ambiente e recompensa (Etapa 10) | — | — | Sim | Sim | ai/environment.py, ai/rewards.py | test_ai.py |
| Replay em arquivo e simulador headless (Etapa 11) | — | — | Sim | Sim | replay.py, simulate.py | test_replay_simulate.py |
