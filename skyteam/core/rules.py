"""Action legality.

There is exactly one implementation of legality: ``violations(ctx, action)`` returns the
list of broken rules as readable sentences. ``get_legal_actions``, ``is_action_legal`` and
``explain_illegal_action`` are all built on it, so they can never disagree.
"""

from __future__ import annotations

from itertools import combinations

from skyteam.mechanics import concentration

from .actions import (
    Action,
    ChooseRerollAction,
    ConfirmStrategyAction,
    DiscardDieAction,
    PassRerollAction,
    PlaceDieAction,
    UseRerollAction,
)
from .context import Hook, RuleContext
from .enums import DecisionKind, GamePhase, Player
from .state import PendingDecision

_ROLE = {Player.PILOT: "Pilot", Player.COPILOT: "Co-Pilot"}


def current_player(ctx: RuleContext) -> Player | None:
    state = ctx.state
    if state.is_terminal:
        return None
    if state.pending:
        return state.pending[0].player
    if state.phase is GamePhase.STRATEGY:
        order = (state.active_player, state.active_player.partner)
        return next((p for p in order if p not in state.strategy_confirmed), None)
    if state.phase is GamePhase.DICE_PLACEMENT:
        return state.active_player
    return None


def _top_decision(ctx: RuleContext) -> PendingDecision | None:
    return ctx.state.pending[0] if ctx.state.pending else None


def _turn_violations(ctx: RuleContext, player: Player, phase: GamePhase) -> list[str]:
    state = ctx.state
    if state.is_terminal:
        return ["The game is over."]
    if state.phase is not phase:
        return [f"This action belongs to the {phase.value} phase; the current phase is {state.phase.value}."]
    if state.pending:
        top = state.pending[0]
        return [f"Waiting for {_ROLE[top.player]} to resolve {top.kind.value}."]
    if current_player(ctx) is not player:
        return [f"It is not the {_ROLE[player]}'s turn."]
    return []


# --------------------------------------------------------------------------- placement
def placement_violations(ctx: RuleContext, action: PlaceDieAction) -> list[str]:
    errors = _turn_violations(ctx, action.player, GamePhase.DICE_PLACEMENT)
    if errors:
        return errors
    state, panel = ctx.state, ctx.panel
    who = _ROLE[action.player]
    if not 0 <= action.die_id < len(state.dice):
        return [f"Die {action.die_id} does not exist."]
    die = state.die(action.die_id)
    if die.owner is not action.player:
        return [f"{who} die {action.die_id} does not belong to the {who}."]
    if die.placed:
        return [f"Die {action.die_id} has already been placed on {die.slot}."]
    if not panel.has_slot(action.slot_id):
        return [f"Space {action.slot_id} does not exist on this Control Panel."]
    slot = panel.slot(action.slot_id)
    if state.slots.get(slot.id) is not None:
        errors.append(f"Space {slot.id} already has a die this round.")
    if action.player not in slot.owners:
        owner = " and ".join(_ROLE[p] for p in sorted(slot.owners, key=lambda p: p.value))
        errors.append(f"{who} die {die.die_id} cannot be placed on {slot.id} because that space belongs to the {owner}.")
    c = ctx.constants
    if action.coffee_delta and not concentration.coffee_change_allowed(
            die.value, action.coffee_delta, state.coffee, c.coffee_max_per_die, c.die_sides):
        errors.append(f"Cannot change a {die.value} by {action.coffee_delta:+d} with {state.coffee} coffee token(s).")
        return errors
    value = die.value + action.coffee_delta
    if not slot.accepts_value(value):
        allowed = "/".join(str(v) for v in sorted(slot.values or ()))
        errors.append(f"Space {slot.id} only accepts {allowed}; the die would show {value}.")
    if slot.requires is not None and not state.switches.get(slot.requires, False):
        errors.append(f"Space {slot.id} must be deployed in order: {slot.requires} first.")
    for fn in ctx.hooks.get(Hook.PLACEMENT_RULES):
        errors.extend(fn(ctx, action))
    return errors


def legal_placements(ctx: RuleContext, player: Player) -> list[PlaceDieAction]:
    if _turn_violations(ctx, player, GamePhase.DICE_PLACEMENT):
        return []
    state = ctx.state
    max_delta = min(state.coffee, ctx.constants.coffee_max_per_die)
    deltas = [0] + [d for k in range(1, max_delta + 1) for d in (-k, k)]
    actions = []
    for die in state.hidden_dice(player):
        for slot in ctx.panel.slots:
            if state.slots.get(slot.id) is not None or player not in slot.owners:
                continue
            for delta in deltas:
                action = PlaceDieAction(player, die.die_id, slot.id, delta)
                if not placement_violations(ctx, action):
                    actions.append(action)
    return actions


# --------------------------------------------------------------------------- other actions
def _strategy_violations(ctx: RuleContext, action: ConfirmStrategyAction) -> list[str]:
    return _turn_violations(ctx, action.player, GamePhase.STRATEGY)


def _discard_violations(ctx: RuleContext, action: DiscardDieAction) -> list[str]:
    errors = _turn_violations(ctx, action.player, GamePhase.DICE_PLACEMENT)
    if errors:
        return errors
    die_ids = {d.die_id for d in ctx.state.hidden_dice(action.player)}
    if action.die_id not in die_ids:
        return [f"Die {action.die_id} is not one of the {_ROLE[action.player]}'s hidden dice."]
    if legal_placements(ctx, action.player):
        return ["A die can only be discarded when no placement is legal (P2)."]
    return []


def _use_reroll_violations(ctx: RuleContext, action: UseRerollAction) -> list[str]:
    state = ctx.state
    if state.is_terminal:
        return ["The game is over."]
    if state.phase is not GamePhase.DICE_PLACEMENT:
        return ["Reroll tokens can only be spent during dice placement."]
    if state.reroll_supply <= 0:
        return ["There is no Reroll token in the supply."]
    top = _top_decision(ctx)
    if top is not None:
        if top.kind is DecisionKind.REROLL_WINDOW and top.player is action.player:
            return []
        return [f"Waiting for {_ROLE[top.player]} to resolve {top.kind.value}."]
    if state.active_player is not action.player:
        return [f"The {_ROLE[action.player]} can spend a reroll on their turn or when offered the reroll window."]
    return []


def _pass_reroll_violations(ctx: RuleContext, action: PassRerollAction) -> list[str]:
    top = _top_decision(ctx)
    if top is None or top.kind is not DecisionKind.REROLL_WINDOW or top.player is not action.player:
        return ["No reroll window is open for this player."]
    return []


def _choose_reroll_violations(ctx: RuleContext, action: ChooseRerollAction) -> list[str]:
    top = _top_decision(ctx)
    if top is None or top.kind is not DecisionKind.REROLL_CHOICE or top.player is not action.player:
        return ["No reroll choice is pending for this player."]
    hidden = {d.die_id for d in ctx.state.hidden_dice(action.player)}
    if len(set(action.die_ids)) != len(action.die_ids):
        return ["A die can only be rerolled once."]
    if not set(action.die_ids) <= hidden:
        return ["Only dice still behind the player's screen can be rerolled."]
    return []


_CHECKS = {
    ConfirmStrategyAction: _strategy_violations,
    PlaceDieAction: placement_violations,
    DiscardDieAction: _discard_violations,
    UseRerollAction: _use_reroll_violations,
    PassRerollAction: _pass_reroll_violations,
    ChooseRerollAction: _choose_reroll_violations,
}


def violations(ctx: RuleContext, action: Action) -> list[str]:
    check = _CHECKS.get(type(action))
    if check is None:
        return [f"Unknown action type {type(action).__name__}."]
    return check(ctx, action)


def legal_actions(ctx: RuleContext, player: Player) -> list[Action]:
    state = ctx.state
    if state.is_terminal or current_player(ctx) is not player:
        return []
    top = _top_decision(ctx)
    if top is not None:
        if top.kind is DecisionKind.REROLL_WINDOW:
            return [UseRerollAction(player), PassRerollAction(player)]
        if top.kind is DecisionKind.REROLL_CHOICE:
            hidden = sorted(d.die_id for d in state.hidden_dice(player))
            return [ChooseRerollAction(player, combo)
                    for n in range(len(hidden) + 1) for combo in combinations(hidden, n)]
        return []
    if state.phase is GamePhase.STRATEGY:
        return [ConfirmStrategyAction(player)]
    if state.phase is GamePhase.DICE_PLACEMENT:
        actions: list[Action] = list(legal_placements(ctx, player))
        if not actions:
            actions = [DiscardDieAction(player, d.die_id) for d in state.hidden_dice(player)]
        if not _use_reroll_violations(ctx, UseRerollAction(player)):
            actions.append(UseRerollAction(player))
        return actions
    return []
