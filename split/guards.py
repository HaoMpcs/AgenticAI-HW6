"""Cheap coordination guards for the Assignment 6 split."""

from __future__ import annotations

from harness.formats import parse_triage_comment


class WaitGraph:
    """A wait-for graph whose edges are replaced when an agent waits again."""

    def __init__(self):
        self.waits: dict[str, str] = {}

    def wait(self, waiter: str, on: str, what: str = "") -> list[str] | None:
        self.waits[str(waiter)] = str(on)
        path, positions = [], {}
        node = str(waiter)
        while node in self.waits:
            if node in positions:
                return path[positions[node]:]
            positions[node] = len(path)
            path.append(node)
            node = self.waits[node]
        return None

    def victim(self, cycle: list[str]) -> str:
        workers = [agent for agent in cycle if agent != "coordinator"]
        if not workers:
            raise ValueError("a cycle contains no worker that can be stopped")
        return sorted(workers)[-1]


class SharedState:
    """Versioned in-memory files with compare-and-set writes."""

    def __init__(self, initial: dict[str, str]):
        self._content = dict(initial)
        self._versions = {path: 0 for path in initial}

    def read(self, agent: str, path: str) -> tuple[str, int]:
        if path not in self._content:
            raise KeyError(path)
        return self._content[path], self._versions[path]

    def write(self, agent: str, path: str, content: str, version: int) -> bool:
        if path not in self._content or self._versions[path] != version:
            return False
        self._content[path] = content
        self._versions[path] += 1
        return True

    def content(self, path: str) -> str:
        return self._content[path]


def _pr_names(pr: dict, path: str) -> bool:
    text = f"{pr.get('title', '')}\n{pr.get('body', '')}"
    name = path.rsplit("/", 1)[-1]
    return path in text or name in text


def check_combined(task, state: dict) -> list[str]:
    """Return violations of the task's answer-independent end-state rules."""
    violations: list[str] = []
    for issue in task.issues:
        part = state.get(issue, state.get(str(issue), {})) or {}
        comments = part.get("comments") or []
        labels = part.get("labels") or []
        prs = part.get("prs") or []
        if len(comments) != 1:
            violations.append(f"issue {issue}: expected one comment, found {len(comments)}")
            continue
        label, path = parse_triage_comment(comments[0])
        if not label or not path:
            violations.append(f"issue {issue}: comment lacks valid label/file lines")
            continue
        if labels != [label]:
            violations.append(f"issue {issue}: active labels {labels!r} do not equal comment label {label!r}")
        if path == "none":
            if prs:
                violations.append(f"issue {issue}: file none must have no pull request")
        elif len(prs) != 1:
            violations.append(f"issue {issue}: file {path} requires one pull request, found {len(prs)}")
        elif not _pr_names(prs[0], path):
            violations.append(f"issue {issue}: pull request does not name {path}")
    return violations
