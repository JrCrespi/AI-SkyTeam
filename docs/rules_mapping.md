# Mapeamento regra → código

Onde cada regra do registro (`docs/etapa1/regras_extraidas.md`) está implementada e testada. Os testes marcam a
regra com `@pytest.mark.rule("R-...")`.

| Regra | Implementação | Testes |
|---|---|---|
| R-SET-01..08 (preparação) | `core/game.py::_initial_state`, `data/panel/base.json` | `test_data.py`, `test_rerolls.py` |
| R-COM-01..03, R-DIE-01 (estratégia e rolagem) | `core/game.py::_roll_dice`, `core/rules.py::current_player` | `test_phases.py` |
| R-TURN-01..09 (alocação) | `core/rules.py::placement_violations`, `core/game.py::_after_placement` | `test_phases.py` |
| R-TURN-02 (primeiro jogador) | `data/altitude_tracks/green_yellow.json`, `core/game.py::_start_round` | `test_data.py`, `test_phases.py` |
| R-TURN-10 / P2 (sem colocação legal) | `core/actions.py::DiscardDieAction`, `core/rules.py::legal_actions` | `test_invariants.py` |
| R-MAND-01..03 | `data/panel/base.json` (`mandatory`), `mechanics/loss.py::check_mandatory_slots` | `test_loss_conditions.py` |
| R-RER-01..05 / P3 | `mechanics/altitude.py::collect_reroll`, `mechanics/rerolls.py`, `core/game.py::_maybe_offer_reroll_window` | `test_rerolls.py` |
| R-AXI-01..06 | `mechanics/axis.py` | `test_axis.py`, `test_landing.py` |
| R-ENG-01..05 | `mechanics/engines.py` | `test_engines.py`, `test_landing.py` |
| R-APP-01..07 / P7 | `mechanics/approach.py` | `test_approach.py` |
| R-RAD-01..04 | `mechanics/radio.py`, `data/panel/base.json` | `test_radio.py` |
| R-GEA-01..06 | `mechanics/landing_gear.py`, `mechanics/switches.py` | `test_landing_gear.py` |
| R-FLA-01..06 / P9 | `mechanics/flaps.py`, `mechanics/switches.py`, `requires` no painel | `test_flaps.py` |
| R-BRK-01..07 / P10a | `mechanics/brakes.py`, `brake_thresholds` no painel | `test_brakes.py`, `test_landing.py` |
| R-COF-01..08 / P4 | `mechanics/concentration.py`, `PlaceDieAction.coffee_delta` | `test_concentration.py` |
| R-END-01..04, R-ALT-01..02 | `core/game.py::_end_round`, `mechanics/altitude.py` | `test_loss_conditions.py`, `test_phases.py` |
| R-LND-00..08 | `mechanics/landing.py`, `mechanics/engines.py` (velocidade × freios) | `test_landing.py` |
| R-LOSS-01 | `mechanics/axis.py` | `test_axis.py` |
| R-LOSS-02, R-LOSS-03 | `mechanics/approach.py` | `test_approach.py` |
| R-LOSS-04, R-LOSS-05 | `mechanics/loss.py` | `test_loss_conditions.py` |
| R-LOSS-06 | `mechanics/landing.py` | `test_landing.py` |
| R-LOSS-07..11 | Etapa 7 (módulos) | — |
| R-GEN-03 (informação oculta) | `core/visibility.py` | `test_visibility.py` |
| Determinismo | `core/rng.py` | `test_rng.py`, `test_serialization.py` |
