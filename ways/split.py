"""Arm M: parallel read-only investigators and serial write-only publishers."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

from agent.loop import load_bounds, run_loop
from harness.schema import errors as schema_errors
from harness.tasks import end_state
from split.guards import check_combined
from split.tools import RestrictedTools
from ways.agent import Disclosing, disclosure_line


def _schema(root: Path) -> dict:
    return json.loads((root / "split" / "contract.schema.json").read_text())


def _investigate(ctx, coordinator, issue: int, share: int, schema: dict) -> tuple[int, dict | None]:
    worker = ctx.agent(f"investigator-{issue}", parent=coordinator.id)
    tools = RestrictedTools(ctx.tools, {"read_issue", "search", "read_file"}, schema)
    bounds = replace(load_bounds(), max_steps=10, max_tokens=max(1, share), wall_clock_s=180)
    run_loop(worker.client, tools, ctx.prompt("investigator.md"), f"Investigate issue #{issue}.", bounds, worker.trace)
    returned = tools.returned[-1] if tools.returned else None
    if returned is not None:
        returned = dict(returned)
        returned["searched"] = tools.coverage()
        returned["calls_used"] = len(tools.course_calls)
    problems = ["worker did not return a contract"] if returned is None else schema_errors(returned, schema)
    valid = not problems and returned["result"].get("issue") == issue
    if not valid and not problems:
        problems = [f"result.issue must be {issue}"]
    coordinator.trace.event("worker_return", worker=worker.id, contract=returned or {},
                            valid=valid, errors=problems)
    return issue, returned if valid else None


def _publish(ctx, coordinator, issue: int, contract: dict, share: int) -> None:
    publisher = ctx.agent(f"publisher-{issue}", parent=coordinator.id)
    base = RestrictedTools(ctx.tools, {"apply_label", "open_pr", "comment"})
    tools = Disclosing(base, disclosure_line())
    result = contract["result"]
    brief = (f"Publish validated issue #{issue}.\nlabel: {result['label']}\nfile: {result['file']}\n"
             f"evidence: {result['evidence']}")
    bounds = replace(load_bounds(), max_steps=5, max_tokens=max(1, share), wall_clock_s=120)
    run_loop(publisher.client, tools, ctx.prompt("publisher.md"), brief, bounds, publisher.trace)


def run(ctx) -> None:
    coordinator = ctx.agent("coordinator")
    issues = list(ctx.issues)
    budget = int(ctx.budget or load_bounds().max_tokens * len(issues))
    investigation_pool = max(1, int(budget * 0.60))
    investigator_share = max(1, investigation_pool // len(issues))
    publisher_share = max(1, int(budget * 0.35) // len(issues))
    schema = _schema(ctx.root)

    for issue in issues:
        coordinator.trace.event("wait", waiter=coordinator.id, on=f"investigator-{issue}",
                                what=f"validated finding for issue {issue}", turn=0)
    findings: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=len(issues)) as pool:
        futures = [pool.submit(_investigate, ctx, coordinator, issue, investigator_share, schema) for issue in issues]
        for future in as_completed(futures):
            issue, contract = future.result()
            if contract is not None:
                findings[issue] = contract

    for issue in issues:
        contract = findings.get(issue)
        if contract is None:
            coordinator.trace.event("worker_stopped", worker=f"publisher-{issue}",
                                    reason="no valid investigator contract")
            continue
        coordinator.trace.event("wait", waiter=coordinator.id, on=f"publisher-{issue}",
                                what=f"writes for issue {issue}", turn=1)
        _publish(ctx, coordinator, issue, contract, publisher_share)

    violations = check_combined(ctx.task, end_state(ctx.tracker, ctx.run_id, ctx.task))
    coordinator.trace.event("combined_check", passed=not violations, violations=violations)
    coordinator.trace.end("model_stopped", "coordination and combined check completed")
