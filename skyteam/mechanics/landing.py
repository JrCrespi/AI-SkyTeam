"""Final round evaluation (MB p.11): R-LND-01..08."""

from __future__ import annotations

from skyteam.core.context import Hook, RuleContext
from skyteam.core.enums import LossReason, WinReason

from . import flaps, landing_gear


def landing_failures(ctx: RuleContext) -> list[tuple[LossReason, str]]:
    """Every unmet condition, in the manual's order A, B, C, D, then module conditions."""
    state = ctx.state
    failures: list[tuple[LossReason, str]] = []
    remaining = sum(state.traffic)
    if remaining:
        failures.append((LossReason.LANDING_TRAFFIC, f"{remaining} airplane(s) still on the approach track"))
    if not (landing_gear.all_deployed(ctx) and flaps.all_deployed(ctx)):
        failures.append((LossReason.LANDING_CONFIGURATION, "landing gear and flaps not fully deployed"))
    if state.axis != 0:
        failures.append((LossReason.LANDING_AXIS, f"axis not horizontal ({state.axis:+d})"))
    if not state.landing_speed_ok:
        failures.append((LossReason.LANDING_SPEED, f"speed {state.last_speed} not below the brakes"))
    for fn in ctx.hooks.get(Hook.LANDING_CHECKS):
        result = fn(ctx)
        if result is not None:
            failures.append(result)
    return failures


def resolve_landing(ctx: RuleContext) -> None:
    failures = landing_failures(ctx)
    if failures:
        reason, text = failures[0]
        ctx.lose(reason, text)
    else:
        ctx.win(WinReason.LANDED, "The plane landed safely. The passengers burst into applause!")
