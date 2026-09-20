"""Helpers for talking to the GTK main loop from worker threads."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_UI_ACTIVE = False


def set_ui_active(active: bool) -> None:
    global _UI_ACTIVE
    _UI_ACTIVE = active


def run_on_ui(func: Callable[[], T], timeout: float = 30.0) -> T:
    if not _UI_ACTIVE or threading.current_thread() is threading.main_thread():
        return func()
    try:
        from gi.repository import GLib
    except Exception:
        return func()

    result: dict[str, object] = {}
    done = threading.Event()

    def wrapper() -> bool:
        try:
            result["value"] = func()
        except Exception as exc:  # pragma: no cover - surfaced to caller
            result["error"] = exc
        finally:
            done.set()
        return False

    GLib.idle_add(wrapper, priority=GLib.PRIORITY_HIGH)
    if not done.wait(timeout):
        raise TimeoutError("GTK main loop did not process the request in time")
    if "error" in result:
        raise result["error"]  # type: ignore[misc]
    return result.get("value")  # type: ignore[return-value]
