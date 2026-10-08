"""State invariants (section 29 of the brief). Used by tests and by debug/strict mode."""

from __future__ import annotations

from .context import RuleContext
from .enums import GamePhase, GameStatus, SlotKind
from .state import DISCARDED


def state_problems(ctx: RuleContext) -> list[str]:
    s, c, panel = ctx.state, ctx.constants, ctx.panel
    problems: list[str] = []

    pieces = [key for key in s.slots.values() if key is not None]
    if len(pieces) != len(set(pieces)):
        problems.append("a piece occupies two spaces")
    for slot_id, key in s.slots.items():
        if not panel.has_slot(slot_id):
            problems.append(f"unknown slot {slot_id} in state")
        if key is not None and key.startswith("die:"):
            die = s.die(int(key[4:]))
            if die.slot != slot_id:
                problems.append(f"slot {slot_id} holds die {die.die_id} but the die says {die.slot}")
    for die in s.dice:
        if die.slot not in (None, DISCARDED) and s.slots.get(die.slot) != f"die:{die.die_id}":
            problems.append(f"die {die.die_id} claims {die.slot} but the slot disagrees")
        if die.value is not None and not 1 <= die.value <= c.die_sides:
            problems.append(f"die {die.die_id} has impossible value {die.value}")
        if die.slot is not None and die.value is None:
            problems.append(f"die {die.die_id} placed without a value")

    if not 0 <= s.coffee <= c.coffee_max:
        problems.append(f"coffee out of range: {s.coffee}")
    if s.reroll_supply < 0 or s.reroll_supply + sum(s.altitude_rerolls) > c.reroll_tokens:
        problems.append("impossible number of reroll tokens")
    if abs(s.axis) >= c.axis_spin_at and s.status is not GameStatus.LOST:
        problems.append(f"axis out of range: {s.axis}")
    if not 0 <= s.brakes_deployed < len(c.brake_thresholds):
        problems.append(f"brakes out of range: {s.brakes_deployed}")

    track = ctx.scenario.approach_track
    if not 0 <= s.approach_position <= track.airport_index:
        problems.append(f"approach position out of range: {s.approach_position}")
    if len(s.traffic) != len(track.spaces) or any(t < 0 for t in s.traffic):
        problems.append("invalid traffic list")
    if s.plane_supply < 0 or s.plane_supply + sum(s.traffic) != c.plane_tokens:
        problems.append("airplane tokens are not conserved")
    if not 0 <= s.altitude_index <= ctx.scenario.altitude_track.final_index:
        problems.append(f"altitude index out of range: {s.altitude_index}")

    for slot in panel.switch_slots():
        if slot.requires and s.switches.get(slot.id) and not s.switches.get(slot.requires):
            problems.append(f"{slot.id} active while {slot.requires} is not")
    if s.aero_blue != c.aero_blue_start + sum(s.switches.get(x.id, False) for x in panel.slots_of(SlotKind.LANDING_GEAR)):
        problems.append("blue aerodynamics marker does not match the landing gear")
    if s.aero_orange != c.aero_orange_start + sum(s.switches.get(x.id, False) for x in panel.slots_of(SlotKind.FLAPS)):
        problems.append("orange aerodynamics marker does not match the flaps")

    terminal = s.status is not GameStatus.IN_PROGRESS
    if terminal != (s.phase is GamePhase.GAME_OVER):
        problems.append("status and phase disagree about the end of the game")
    if terminal and not s.terminal_reason:
        problems.append("terminal state without a reason")
    return problems

