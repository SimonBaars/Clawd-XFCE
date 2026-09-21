"""Bash, text-editor, memory, and expression tools."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from clippy_xfce.agent.memory import MemoryStore

DANGEROUS_BASH = re.compile(
    r"""(?xi)
    \b(
        rm\s|shred|mkfs|dd\s|shutdown|reboot|halt|poweroff|
        sudo|doas|passwd|userdel|chmod\s+777|chown\s|
        curl.+\|\s*(ba)?sh|wget.+\|\s*(ba)?sh|
        xkill|killall|pkill|\bkill\s
    )
    """
)

CUSTOM_TOOLS = [
    {
        "name": "remember",
        "description": "Store a durable fact about the user, their preferences, or this machine for future conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The fact to remember."},
                "kind": {
                    "type": "string",
                    "enum": ["fact", "preference", "project", "people"],
                    "description": "Memory category.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "recall",
        "description": "Search long-term memories from past conversations.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "express",
        "description": "Play a Clippy animation so the on-screen assistant looks expressive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mood": {
                    "type": "string",
                    "enum": [
                        "idle",
                        "greet",
                        "think",
                        "search",
                        "write",
                        "talk",
                        "act",
                        "success",
                        "error",
                        "bye",
                    ],
                },
                "animation": {
                    "type": "string",
                    "description": "Exact clippy.js animation name, if you want a specific one.",
                },
            },
        },
    },
    {
        "name": "flash",
        "description": (
            "Show a short on-screen caption the user can read while you use the computer. "
            "Use this to explain the current step when they asked you to teach or walk them through it. "
            "One or two sentences. Do not flash secrets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Caption the user will see."},
                "seconds": {
                    "type": "number",
                    "description": "How long to leave it up, from 2 to 12. Default 5.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "notify_user",
        "description": "Same as flash: show a short live caption on the desktop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "text": {"type": "string"},
                "seconds": {"type": "number"},
            },
            "required": ["body"],
        },
    },
    {
        "name": "watch_window",
        "description": (
            "Block locally until a desktop window looks idle. Uses title and a tiny "
            "frame hash — no screenshots are sent to Claude while waiting. Use this "
            "instead of screenshot+wait loops when babysitting another agent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "window": {
                    "type": "string",
                    "description": "'active' or a title/app substring such as cursor.",
                },
                "idle_seconds": {
                    "type": "number",
                    "description": "How long the window must stay still. Default 8.",
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Give up after this many seconds. 0 means no limit.",
                },
                "require_busy": {
                    "type": "boolean",
                    "description": "Wait for activity first, then idle (default true).",
                },
            },
        },
    },
    {
        "name": "supervise",
        "description": (
            "Start a repeating local watcher. After this turn ends, Clippy watches "
            "the window for free and only wakes you when it goes idle. Call this "
            "when the user wants monitoring or 'every time it finishes'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "window": {"type": "string"},
                "idle_seconds": {"type": "number"},
                "timeout_seconds": {"type": "number"},
                "require_busy": {"type": "boolean"},
                "on_idle": {
                    "type": "string",
                    "description": "What to do each time the window goes idle.",
                },
            },
        },
    },
    {
        "name": "stop_supervise",
        "description": "Stop the repeating local watcher.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def is_dangerous_bash(command: str) -> bool:
    return bool(DANGEROUS_BASH.search(command))


def run_bash(command: str, cwd: str | None = None, timeout: float = 60.0) -> str:
    env = os.environ.copy()
    completed = subprocess.run(
        ["bash", "-lc", command],
        cwd=cwd or os.path.expanduser("~"),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    out = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        out = f"exit {completed.returncode}\n{out}"
    return out[-12000:] or "(no output)"


class TextEditor:
    def __init__(self) -> None:
        self._history: dict[str, str] = {}

    def handle(self, payload: dict[str, Any]) -> str:
        command = payload.get("command") or payload.get("action")
        path = Path(os.path.expanduser(str(payload.get("path") or ""))).resolve()
        if command == "view":
            if not path.exists():
                raise FileNotFoundError(str(path))
            if path.is_dir():
                names = sorted(item.name + ("/" if item.is_dir() else "") for item in path.iterdir())
                return "\n".join(names[:400]) or "(empty directory)"
            text = path.read_text(encoding="utf-8", errors="replace")
            start = int(payload.get("view_range", [1, -1])[0] if payload.get("view_range") else 1)
            end = int(payload.get("view_range", [1, -1])[1] if payload.get("view_range") else -1)
            lines = text.splitlines()
            lo = max(1, start)
            hi = len(lines) if end < 0 else min(len(lines), end)
            numbered = [f"{i:>6}|{lines[i - 1]}" for i in range(lo, hi + 1)]
            return "\n".join(numbered) or "(empty file)"
        if command == "create":
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                self._history[str(path)] = path.read_text(encoding="utf-8", errors="replace")
            path.write_text(str(payload.get("file_text") or ""), encoding="utf-8")
            return f"wrote {path}"
        if command == "str_replace":
            old = str(payload.get("old_str") or "")
            new = str(payload.get("new_str") or "")
            text = path.read_text(encoding="utf-8")
            count = text.count(old)
            if count != 1:
                raise ValueError(f"old_str matched {count} times; need exactly 1")
            self._history[str(path)] = text
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return f"updated {path}"
        if command == "insert":
            insert = str(payload.get("insert_text") or payload.get("new_str") or "")
            line = int(payload.get("insert_line") or 1)
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            self._history[str(path)] = text
            lines = text.splitlines(keepends=True)
            idx = max(0, min(len(lines), line - 1))
            if insert and not insert.endswith("\n"):
                insert += "\n"
            lines.insert(idx, insert)
            path.write_text("".join(lines), encoding="utf-8")
            return f"inserted into {path}"
        if command == "undo_edit":
            if str(path) not in self._history:
                raise ValueError("nothing to undo")
            path.write_text(self._history.pop(str(path)), encoding="utf-8")
            return f"restored {path}"
        raise ValueError(f"Unknown editor command: {command}")


class ToolHub:
    def __init__(
        self,
        memory: MemoryStore,
        express: Callable[[str, str | None], str] | None = None,
        flash: Callable[[str, float], str] | None = None,
        watch: Callable[[dict[str, Any]], str] | None = None,
        supervise: Callable[[dict[str, Any]], str] | None = None,
        stop_supervise: Callable[[], str] | None = None,
    ) -> None:
        self.memory = memory
        self.editor = TextEditor()
        self.express = express
        self.flash = flash
        self.watch = watch
        self.supervise = supervise
        self.stop_supervise = stop_supervise

    def handle(self, name: str, payload: dict[str, Any]) -> str:
        if name in {"bash", "bash_20250124"}:
            return run_bash(str(payload.get("command") or ""))
        if name in {
            "str_replace_based_edit_tool",
            "str_replace_editor",
            "text_editor",
        }:
            return self.editor.handle(payload)
        if name == "remember":
            item = self.memory.remember(str(payload.get("text") or ""), str(payload.get("kind") or "fact"))
            return f"remembered #{item.id}"
        if name == "recall":
            hits = self.memory.search_memories(str(payload.get("query") or ""))
            if not hits:
                return "no memories matched"
            return "\n".join(f"- ({hit.kind}) {hit.text}" for hit in hits)
        if name == "express":
            if not self.express:
                return "expression unavailable"
            return self.express(str(payload.get("mood") or "talk"), payload.get("animation"))
        if name in {"flash", "notify_user"}:
            caption = str(payload.get("text") or payload.get("body") or "").strip()
            seconds = payload.get("seconds", 5)
            try:
                hold = float(seconds)
            except (TypeError, ValueError):
                hold = 5.0
            if self.flash:
                return self.flash(caption, hold)
            title = str(payload.get("title") or "Clippy")
            if caption and shutil.which("notify-send"):
                subprocess.Popen(
                    ["notify-send", "-a", "Clippy", title, caption],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return "flashed" if caption else "nothing to flash"
        if name == "watch_window":
            if not self.watch:
                return "watch unavailable"
            return self.watch(payload)
        if name == "supervise":
            if not self.supervise:
                return "supervise unavailable"
            return self.supervise(payload)
        if name == "stop_supervise":
            if not self.stop_supervise:
                return "supervise unavailable"
            return self.stop_supervise()
        raise ValueError(f"Unknown tool: {name}")
