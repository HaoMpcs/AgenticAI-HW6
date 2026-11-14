"""Restricted tool surfaces and the investigator's local return tool."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from harness.roles import arg, role_of
from tools import ToolResult


RETURN_NAME = "submit_investigation"


@dataclass
class RestrictedTools:
    tools: object
    allowed_roles: set[str]
    return_schema: dict | None = None
    returned: list[dict] = field(default_factory=list)
    course_calls: list[tuple[str, dict]] = field(default_factory=list)

    @property
    def schemas(self) -> list[dict]:
        offered = [schema for schema in self.tools.schemas if role_of(schema["name"]) in self.allowed_roles]
        if self.return_schema is not None:
            offered.append({
                "name": RETURN_NAME,
                "strict": True,
                "description": "Return the investigation once. State uncertainty explicitly; do not claim searches not made.",
                "input_schema": self.return_schema,
            })
        return offered

    def call(self, name: str, tool_input: dict, **kwargs):
        if name == RETURN_NAME and self.return_schema is not None:
            self.returned.append(copy.deepcopy(tool_input))
            return ToolResult("Investigation returned to the coordinator.", False, 0.0)
        role = role_of(name)
        if role not in self.allowed_roles:
            return ToolResult("This role is not allowed to use that tool.", True, 0.0)
        self.course_calls.append((name, copy.deepcopy(tool_input)))
        return self.tools.call(name, tool_input, **kwargs)

    def coverage(self) -> list[str]:
        """Coverage facts derived from calls, never from the model's return."""
        values: list[str] = []
        for name, call in self.course_calls:
            role = role_of(name)
            key = arg("search", "query") if role == "search" else arg("read_file", "path") if role == "read_file" else None
            value = call.get(key) if key else None
            if value is not None and str(value) not in values:
                values.append(str(value))
        return values
