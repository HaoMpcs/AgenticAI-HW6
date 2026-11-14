"""Arm S-plus: sequential fresh-context attempts, then one voted answer is written once."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace

from agent.loop import load_bounds, run_loop
from harness.schema import errors as schema_errors
from harness.tasks import end_state
from split.guards import check_combined
from split.tools import RestrictedTools
from ways.agent import Disclosing, disclosure_line


def _attempt(ctx, issue: int, number: int, cap: int, schema: dict) -> dict | None:
    agent = ctx.agent(f"attempt-{number}-{issue}")
    tools = RestrictedTools(ctx.tools, {"read_issue", "search", "read_file"}, schema)
    bounds = replace(load_bounds(), max_steps=10, max_tokens=max(1, cap), wall_clock_s=180)
    run_loop(agent.client, tools, ctx.prompt("investigator.md"), f"Independently investigate issue #{issue}.",
             bounds, agent.trace)
    if not tools.returned:
        return None
    contract = dict(tools.returned[-1])
    contract["searched"] = tools.coverage()
    contract["calls_used"] = len(tools.course_calls)
    if schema_errors(contract, schema) or contract["result"].get("issue") != issue:
        return None
    return contract


def _choose(contracts: list[dict]) -> dict | None:
    """Majority over independently proposed label/file pairs; stable first-result tie break."""
    if not contracts:
        return None
    pairs = [(c["result"]["label"], c["result"]["file"]) for c in contracts]
    counts = Counter(pairs)
    winner = max(pairs, key=lambda pair: (counts[pair], -pairs.index(pair)))
    return next(c for c, pair in zip(contracts, pairs) if pair == winner)


def _write(ctx, issue: int, number: int, contract: dict, cap: int) -> None:
    agent = ctx.agent(f"write-{number}-{issue}")
    tools = Disclosing(RestrictedTools(ctx.tools, {"apply_label", "open_pr", "comment"}), disclosure_line())
    result = contract["result"]
    brief = (f"Publish the selected answer for issue #{issue}.\nlabel: {result['label']}\n"
             f"file: {result['file']}\nevidence: {result['evidence']}")
    bounds = replace(load_bounds(), max_steps=5, max_tokens=max(1, cap), wall_clock_s=120)
    run_loop(agent.client, tools, ctx.prompt("publisher.md"), brief, bounds, agent.trace)


def run(ctx) -> None:
    issues = list(ctx.issues)
    budget = int(ctx.budget or load_bounds().max_tokens * len(issues))
    slice_budget = max(1, budget // len(issues))
    schema = json.loads((ctx.root / "split" / "contract.schema.json").read_text())

    for issue in issues:
        start = ctx.client.total_tokens
        contracts: list[dict] = []
        attempt = 0
        # Spend up to roughly 65% of this issue's matched allowance on sequential,
        # fresh-context read attempts. Reserve the remainder for the single write.
        while ctx.client.total_tokens - start < int(slice_budget * 0.65) and attempt < 4:
            attempt += 1
            remaining_read = max(1, int(slice_budget * 0.70) - (ctx.client.total_tokens - start))
            contract = _attempt(ctx, issue, attempt, remaining_read, schema)
            if contract is not None:
                contracts.append(contract)
        chosen = _choose(contracts)
        if chosen is not None:
            spent = ctx.client.total_tokens - start
            _write(ctx, issue, attempt + 1, chosen, max(1, slice_budget - spent))

    violations = check_combined(ctx.task, end_state(ctx.tracker, ctx.run_id, ctx.task))
    ctx.trace.event("combined_check", passed=not violations, violations=violations)
