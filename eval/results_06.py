#!/usr/bin/env python3
"""Recompute Assignment 6 measured outcomes from traces and tracker state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from eval.check_task import check_task
from harness import LAB, ROOT
from harness.runner import is_free, is_trace
from harness.tasks import load_tasks
from harness.trace import read_trace
from harness.tracker import Tracker


ARMS = {"agent": "S", "split": "M", "splus": "S_plus"}


def rows(root: Path = ROOT) -> list[dict]:
    tasks = {task.id: task for task in load_tasks(root / "fixtures" / "tasks6")}
    tracker = Tracker(root, flaky=False, readback_fail=False)
    output: list[dict] = []
    for path in sorted((root / "runs").glob("*.jsonl")):
        if not is_trace(path):
            continue
        records = read_trace(path)
        if not records or records[0].get("type") != "run_start":
            continue
        start = records[0]
        way, task_id = start.get("way"), start.get("task")
        if start.get("lab") != LAB or way not in ARMS or task_id not in tasks or is_free(start.get("backend") or ""):
            continue
        end = records[-1] if records[-1].get("type") == "run_end" else None
        reasons = {record.get("terminal_reason") for record in records if record.get("type") == "end"}
        if end is None or {"quota", "rate_limited"} & reasons:
            continue
        checked = check_task(start["run_id"], tasks[task_id], tracker=tracker)
        output.append({
            "run_id": start["run_id"], "arm": ARMS[way], "way": way,
            "task": task_id, "kind": start["kind"], "sweep": start["sweep"],
            "passed": checked["passed"],
            "parts": {str(issue): passed for issue, passed in checked["parts"].items()},
            "tokens": int((end.get("totals") or {}).get("total_tokens") or 0),
            "wall_s": float(end.get("elapsed_s") or 0.0),
        })
    return sorted(output, key=lambda row: (row["arm"], row["task"], row["sweep"], row["run_id"]))


def main() -> None:
    destination = ROOT / "results" / "runs_06.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    values = rows()
    destination.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in values))
    print(f"wrote {len(values)} measured runs to {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
