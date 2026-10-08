# Matriz de cobertura das regras

Atualizada ao fim de cada etapa. Situação atual: **Etapa 1 concluída e conferida com os manuais oficiais em inglês**, sem nada implementado.

"Fonte" indica a situação da regra no registro (`docs/etapa1/regras_extraidas.md`):
**Manual** (confirmada no texto), **Parcial** (há itens de ilustração, inferidos ou ambíguos) ou **Falta componente**.

| Regra/Mecânica | Ids | Fonte | Implementada | Testada | Arquivo | Teste |
|---|---|---|---|---|---|---|
| Preparação | R-SET-* | Manual | Não | Não | scenarios/loader.py | test_setup.py |
| Fases e comunicação | R-GEN-04, R-COM-* | Manual | Não | Não | core/phases.py | test_phases.py |
| Turnos e colocação | R-TURN-* | Parcial (P2) | Não | Não | core/rules.py | test_placement.py |
| Ações obrigatórias | R-MAND-* | Manual | Não | Não | mechanics/loss.py | test_loss_conditions.py |
| Dados | R-DIE-* | Manual | Não | Não | core/dice.py | test_dice.py |
| Rerrolagem | R-RER-* | Parcial (P3, P12b) | Não | Não | mechanics/rerolls.py | test_rerolls.py |
| Eixo | R-AXI-* | Parcial (P21) | Não | Não | mechanics/axis.py | test_axis.py |
| Motores | R-ENG-* | Manual | Não | Não | mechanics/engines.py | test_engines.py |
| Aproximação | R-APP-* | Parcial (P7, P12) | Não | Não | mechanics/approach.py | test_approach.py |
| Rádio | R-RAD-* | Manual | Não | Não | mechanics/radio.py | test_radio.py |
| Trem de pouso | R-GEA-* | Manual (valores por ilustração) | Não | Não | mechanics/landing_gear.py | test_landing_gear.py |
| Flaps | R-FLA-* | Parcial (P9) | Não | Não | mechanics/flaps.py | test_flaps.py |
| Freios | R-BRK-* | Parcial (P10) | Não | Não | mechanics/brakes.py | test_brakes.py |
| Concentração / Café | R-COF-* | Parcial (P4) | Não | Não | mechanics/concentration.py | test_concentration.py |
| Fim de rodada / Altitude | R-END-*, R-ALT-* | Parcial (P12b) | Não | Não | mechanics/altitude.py | test_altitude.py |
| Pouso (vitória A–D) | R-LND-* | Manual | Não | Não | mechanics/landing.py | test_landing.py |
| Derrotas (11 condições) | R-LOSS-* | Manual | Não | Não | mechanics/loss.py | test_loss_conditions.py |
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
| Cenários (21) | seção 18 | Parcial (pistas: P12) | Não | Não | data/scenarios/ | test_scenarios.py |
| Aeroportos (11) | seção 16 | Manual | Não | Não | data/airports/ | test_scenarios.py |
