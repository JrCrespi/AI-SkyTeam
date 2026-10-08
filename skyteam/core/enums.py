"""Enumerations shared by the whole engine."""

from __future__ import annotations

from enum import Enum


class Player(str, Enum):
    PILOT = "pilot"
    COPILOT = "copilot"

    @property
    def partner(self) -> "Player":
        return Player.COPILOT if self is Player.PILOT else Player.PILOT


PLAYERS: tuple[Player, Player] = (Player.PILOT, Player.COPILOT)


class GamePhase(str, Enum):
    """Official phases (MB p.4) plus engine bookkeeping phases.

    ROUND_START, DICE_ROLL and ROUND_END are resolved automatically by the engine;
    players only act during STRATEGY and DICE_PLACEMENT.
    """

    ROUND_START = "round_start"
    STRATEGY = "strategy"
    DICE_ROLL = "dice_roll"
    DICE_PLACEMENT = "dice_placement"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class LossReason(str, Enum):
    """One value per official loss condition (docs/etapa1/regras_extraidas.md §15)."""

    AXIS_SPIN = "axis_spin"                          # R-LOSS-01
    COLLISION = "collision"                          # R-LOSS-02
    OVERSHOOT = "overshoot"                          # R-LOSS-03
    MANDATORY_SLOT_EMPTY = "mandatory_slot_empty"    # R-LOSS-04
    CRASH_BEFORE_AIRPORT = "crash_before_airport"    # R-LOSS-05
    LANDING_TRAFFIC = "landing_traffic"              # R-LOSS-06 / R-LND-01
    LANDING_CONFIGURATION = "landing_configuration"  # R-LOSS-06 / R-LND-02
    LANDING_AXIS = "landing_axis"                    # R-LOSS-06 / R-LND-03
    LANDING_SPEED = "landing_speed"                  # R-LOSS-06 / R-LND-04
    OUT_OF_KEROSENE = "out_of_kerosene"              # R-LOSS-07
    INTERN_UNTRAINED = "intern_untrained"            # R-LOSS-08
    TIME_EXPIRED = "time_expired"                    # R-LOSS-09
    ICE_BRAKES_INCOMPLETE = "ice_brakes_incomplete"  # R-LOSS-10
    TURN_AXIS = "turn_axis"                          # R-LOSS-11


class WinReason(str, Enum):
    LANDED = "landed"


class SlotKind(str, Enum):
    AXIS = "axis"
    ENGINES = "engines"
    RADIO = "radio"
    LANDING_GEAR = "landing_gear"
    FLAPS = "flaps"
    BRAKES = "brakes"
    CONCENTRATION = "concentration"
    MODULE = "module"


class DecisionKind(str, Enum):
    """Interruptions that temporarily give the turn to a specific player."""

    REROLL_WINDOW = "reroll_window"    # non-active player may spend a reroll token (P3)
    REROLL_CHOICE = "reroll_choice"    # each player picks which hidden dice to reroll (R-RER-03)
