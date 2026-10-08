"""``SkyTeamGame``: the orchestrator.

It owns the configuration (panel, scenario, hooks), the mutable ``GameState`` and the
history, and sequences the phases. All rules live in ``skyteam.mechanics`` and
``skyteam.core.rules``; this class only decides *when* they run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from skyteam.mechanics import (
    altitude,
    axis,
    brakes,
    concentration,
    engines,
    flaps,
    landing,
    landing_gear,
    loss,
    radio,
    rerolls,
)
from skyteam.scenarios.model import Scenario

from . import rules
from .actions import (
    Action,
    ChooseRerollAction,
    ConfirmStrategyAction,
    DiscardDieAction,
    PassRerollAction,
    PlaceDieAction,
    UseRerollAction,
)
from .context import Hook, HookRegistry, RuleContext
from .enums import PLAYERS, DecisionKind, GamePhase, GameStatus, Player, SlotKind
from .events import EventBus, EventType, GameEvent
from .exceptions import IllegalActionError, InvalidStateError
from .panel import PanelLayout, load_panel
from .rng import RngStreams
from .state import DISCARDED, DieState, GameState, PendingDecision
from .validation import state_problems
from .visibility import structured_observation, visible_events

RNG_STREAMS = ("dice", "traffic")

Resolver = Callable[[RuleContext, str, int], None]

SLOT_RESOLVERS: dict[SlotKind, Resolver] = {
    SlotKind.AXIS: axis.on_placed,
    SlotKind.ENGINES: engines.on_placed,
    SlotKind.RADIO: radio.on_placed,
    SlotKind.LANDING_GEAR: landing_gear.on_placed,
    SlotKind.FLAPS: flaps.on_placed,
    SlotKind.BRAKES: brakes.on_placed,
    SlotKind.CONCENTRATION: concentration.on_placed,
}


@dataclass(frozen=True, slots=True)
class StepResult:
    events: list[GameEvent]
    status: GameStatus
    terminal_reason: str | None
    next_player: Player | None


@dataclass(slots=True)
class _Snapshot:
    state: GameState
    n_events: int
    n_actions: int


@dataclass(slots=True)
class GameConfig:
    strict: bool = False             # validate invariants after every action
    debug: bool = False              # enables the debug_* helpers (section 26); implies strict
    keep_undo: bool = True           # keep snapshots for undo_action()


@dataclass(slots=True)
class _Runtime:
    events: list[GameEvent] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    undo: list[_Snapshot] = field(default_factory=list)


class SkyTeamGame:
    def __init__(self, scenario: Scenario, panel: PanelLayout | None = None,
                 config: GameConfig | None = None, hooks: HookRegistry | None = None) -> None:
        self.scenario = scenario
        self.panel = panel or load_panel(scenario.panel)
        self.config = config or GameConfig()
        self.hooks = hooks or HookRegistry()
        self.bus = EventBus()
        self._rt = _Runtime()
        self.state: GameState = GameState(scenario_id=scenario.id, seed=0)
        if scenario.modules:
            raise NotImplementedError(
                f"scenario {scenario.id} uses modules {[m.id for m in scenario.modules]}, "
                "which arrive in Etapa 7")

    # ================================================================== public API
    def reset(self, seed: int = 0) -> GameState:
        self._rt = _Runtime()
        self.state = self._initial_state(seed)
        ctx = self._ctx()
        ctx.emit(EventType.GAME_STARTED, f"Game started: {self.scenario.id} (seed {seed})",
                 scenario=self.scenario.id)
        self._start_round(ctx)
        return self.state

    @property
    def current_player(self) -> Player | None:
        return rules.current_player(self._ctx())

    def get_state(self) -> GameState:
        return self.state

    get_full_state = get_state

    def get_legal_actions(self, player: Player | None = None) -> list[Action]:
        player = player or self.current_player
        if player is None:
            return []
        return rules.legal_actions(self._ctx(), player)

    def is_action_legal(self, action: Action) -> bool:
        return not rules.violations(self._ctx(), action)

    def explain_illegal_action(self, action: Action) -> list[str]:
        return rules.violations(self._ctx(), action)

    def step(self, action: Action) -> StepResult:
        ctx = self._ctx()
        problems = rules.violations(ctx, action)
        if problems:
            raise IllegalActionError(problems)
        if self.config.keep_undo:
            self._rt.undo.append(_Snapshot(self.state.copy(), len(self._rt.events), len(self._rt.actions)))
        first_event = len(self._rt.events)
        self._rt.actions.append(action)
        self._apply(ctx, action)
        if self.config.strict or self.config.debug:
            self.validate_state(raise_on_error=True)
        return StepResult(self._rt.events[first_event:], self.state.status, self.state.terminal_reason,
                          self.current_player)

    apply_action = step

    def undo_action(self) -> None:
        if not self._rt.undo:
            raise IndexError("nothing to undo")
        snap = self._rt.undo.pop()
        self.state = snap.state
        del self._rt.events[snap.n_events:]
        del self._rt.actions[snap.n_actions:]

    def clone(self) -> "SkyTeamGame":
        other = SkyTeamGame.__new__(SkyTeamGame)
        other.scenario, other.panel, other.config, other.hooks = self.scenario, self.panel, self.config, self.hooks
        other.bus = self.bus
        other.state = self.state.copy()
        other._rt = _Runtime(list(self._rt.events), list(self._rt.actions), [])
        return other

    def save_state(self) -> dict[str, Any]:
        return self.state.to_dict()

    def load_state(self, snapshot: dict[str, Any]) -> None:
        state = GameState.from_dict(snapshot)
        if state.scenario_id != self.scenario.id:
            raise ValueError(f"snapshot is for scenario {state.scenario_id}, not {self.scenario.id}")
        self.state = state
        self._rt.undo.clear()

    def is_terminal(self) -> bool:
        return self.state.is_terminal

    def get_result(self) -> tuple[GameStatus, str | None]:
        return self.state.status, self.state.terminal_reason

    def get_observation(self, player: Player) -> dict[str, Any]:
        return structured_observation(self._ctx(), player)

    def validate_state(self, raise_on_error: bool = False) -> list[str]:
        problems = state_problems(self._ctx())
        if problems and raise_on_error:
            raise InvalidStateError(problems)
        return problems

    @property
    def events(self) -> list[GameEvent]:
        return self._rt.events

    @property
    def actions(self) -> list[Action]:
        return self._rt.actions

    def history(self, player: Player | None = None) -> list[str]:
        """Readable log. With ``player``, only what that player may know."""
        events = self._rt.events if player is None else visible_events(self._rt.events, player)
        lines, current_round = [], None
        for e in events:
            if e.round != current_round and e.round > 0:
                current_round = e.round
                lines.append(f"Round {e.round}")
            lines.append(f"  {e.text}")
        return lines

    # ================================================================== debug mode
    def debug_set_dice(self, values: dict[int, int]) -> None:
        """Debug only: overwrite the value of hidden dice (``{die_id: value}``)."""
        self._require_debug()
        for die_id, value in values.items():
            die = self.state.die(die_id)
            if die.placed or die.value is None:
                raise ValueError(f"die {die_id} is not a rolled hidden die")
            if not 1 <= value <= self.panel.constants.die_sides:
                raise ValueError(f"impossible die value {value}")
            die.value = value
        self._ctx().emit(EventType.DICE_ROLLED, f"[debug] dice values set: {values}", private_to=None,
                         debug=True, values={str(k): v for k, v in values.items()})
        self.validate_state(raise_on_error=True)

    def _require_debug(self) -> None:
        if not self.config.debug:
            raise PermissionError("debug helpers require GameConfig(debug=True)")

    # ================================================================== flow
    def _ctx(self) -> RuleContext:
        return RuleContext(self.state, self.panel, self.scenario, self.bus, self.hooks, self._rt.events)

    def _initial_state(self, seed: int) -> GameState:
        c = self.panel.constants
        approach, alt = self.scenario.approach_track, self.scenario.altitude_track
        traffic = [s.traffic for s in approach.spaces]
        dice = [DieState(i, PLAYERS[i // c.dice_per_player]) for i in range(2 * c.dice_per_player)]
        return GameState(
            scenario_id=self.scenario.id,
            seed=seed,
            dice=dice,
            slots={s.id: None for s in self.panel.slots},
            switches={s.id: False for s in self.panel.switch_slots()},
            aero_blue=c.aero_blue_start,
            aero_orange=c.aero_orange_start,
            altitude_rerolls=[s.reroll for s in alt.spaces],
            traffic=traffic,
            plane_supply=c.plane_tokens - sum(traffic),
            rng=RngStreams.initial(seed, RNG_STREAMS),
        )

    def _start_round(self, ctx: RuleContext) -> None:
        state = ctx.state
        state.round += 1
        state.phase = GamePhase.ROUND_START
        space = altitude.current_space(ctx)
        state.active_player = space.first_player
        state.strategy_confirmed = []
        state.last_speed = None
        label = "landing" if space.final else f"{space.altitude} ft"
        ctx.emit(EventType.ROUND_STARTED, f"Round {state.round} begins at {label}; "
                 f"{space.first_player.value} plays first", first_player=space.first_player.value)
        if space.final:
            ctx.emit(EventType.LANDING_STARTED, "Final round: engines are compared with the brakes")
        altitude.collect_reroll(ctx)
        for fn in ctx.hooks.get(Hook.ROUND_START):
            fn(ctx)
            if state.is_terminal:
                return
        state.phase = GamePhase.STRATEGY

    def _roll_dice(self, ctx: RuleContext) -> None:
        state = ctx.state
        state.phase = GamePhase.DICE_ROLL
        for die in state.dice:
            die.value = ctx.rng.roll("dice", ctx.constants.die_sides)
        ctx.emit(EventType.DICE_ROLLED, "Both players roll their dice behind their screens")
        for player in PLAYERS:
            values = [d.value for d in state.dice_of(player)]
            ctx.emit(EventType.DICE_ROLLED, f"{player.value} rolled {values}", private_to=player.value,
                     player=player.value, values=values)
        state.phase = GamePhase.DICE_PLACEMENT
        self._open_turn(ctx)

    def _open_turn(self, ctx: RuleContext) -> None:
        """Offer the reroll window to the non-active player once per turn.

        TODO_RULE_VERIFICATION P3: digital equivalent of "at any time, any player" (MB p.4).
        """
        state = ctx.state
        state.reroll_window_done = False
        self._maybe_offer_reroll_window(ctx)

    def _maybe_offer_reroll_window(self, ctx: RuleContext) -> None:
        state = ctx.state
        if state.reroll_window_done or state.reroll_supply <= 0 or state.pending:
            return
        state.reroll_window_done = True
        state.pending.append(PendingDecision(DecisionKind.REROLL_WINDOW, state.active_player.partner))

    def _apply(self, ctx: RuleContext, action: Action) -> None:
        state = ctx.state
        if isinstance(action, ConfirmStrategyAction):
            state.strategy_confirmed.append(action.player)
            ctx.emit(EventType.STRATEGY_CONFIRMED, f"{action.player.value} is ready", player=action.player.value)
            if len(state.strategy_confirmed) == len(PLAYERS):
                self._roll_dice(ctx)
        elif isinstance(action, PlaceDieAction):
            self._place(ctx, action)
        elif isinstance(action, DiscardDieAction):
            die = state.die(action.die_id)
            die.slot = DISCARDED
            ctx.emit(EventType.DIE_DISCARDED, f"{action.player.value} discards a die (no legal placement)",
                     player=action.player.value, die_id=die.die_id)
            self._after_placement(ctx)
        elif isinstance(action, UseRerollAction):
            if state.pending and state.pending[0].kind is DecisionKind.REROLL_WINDOW:
                state.pending.pop(0)
            rerolls.spend_token(ctx, action.player)
        elif isinstance(action, PassRerollAction):
            state.pending.pop(0)
        elif isinstance(action, ChooseRerollAction):
            state.pending.pop(0)
            rerolls.reroll(ctx, action.player, action.die_ids)

    def _place(self, ctx: RuleContext, action: PlaceDieAction) -> None:
        state = ctx.state
        die = state.die(action.die_id)
        rolled = die.value
        die.value += action.coffee_delta
        die.slot = action.slot_id
        state.slots[action.slot_id] = f"die:{die.die_id}"
        coffee = f" (a {rolled} changed with coffee)" if action.coffee_delta else ""
        ctx.emit(EventType.DIE_PLACED, f"{action.player.value} places a {die.value} on {action.slot_id}{coffee}",
                 player=action.player.value, die_id=die.die_id, slot=action.slot_id, value=die.value,
                 coffee_delta=action.coffee_delta)
        concentration.spend(ctx, action.coffee_delta)
        slot = self.panel.slot(action.slot_id)
        SLOT_RESOLVERS[slot.kind](ctx, slot.id, die.value)
        if state.is_terminal:
            return
        self._after_placement(ctx)

    def _after_placement(self, ctx: RuleContext) -> None:
        state = ctx.state
        if not any(state.hidden_dice(p) for p in PLAYERS):
            self._end_round(ctx)
            return
        partner = state.active_player.partner
        if state.hidden_dice(partner):
            state.active_player = partner
        self._open_turn(ctx)

    def _end_round(self, ctx: RuleContext) -> None:
        state = ctx.state
        state.phase = GamePhase.ROUND_END
        state.pending.clear()
        ctx.emit(EventType.ROUND_ENDED, f"Round {state.round} ends")
        loss.check_mandatory_slots(ctx)
        if state.is_terminal:
            return
        if altitude.is_final_round(ctx):
            loss.check_game_end(ctx)
            if not state.is_terminal:
                landing.resolve_landing(ctx)
            return
        altitude.descend(ctx)
        self._return_dice(ctx)
        loss.check_reached_airport_in_time(ctx)
        if state.is_terminal:
            return
        for fn in ctx.hooks.get(Hook.ROUND_END_FINAL_STEP):
            fn(ctx)
            if state.is_terminal:
                return
        self._start_round(ctx)

    @staticmethod
    def _return_dice(ctx: RuleContext) -> None:
        state = ctx.state
        for die in state.dice:
            die.slot = None
            die.value = None
        for slot_id in state.slots:
            state.slots[slot_id] = None
