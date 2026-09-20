"""Live XFCE / X11 desktop context for Claude."""

from __future__ import annotations

import datetime as dt
import getpass
import os
import platform
import shutil
import socket
import subprocess
from typing import Any

from clippy_xfce.gtkutil import run_on_ui


def clipboard_text(limit: int = 800) -> str:
    if not shutil.which("xclip"):
        return ""
    try:
        raw = subprocess.check_output(
            ["xclip", "-selection", "clipboard", "-o"],
            stderr=subprocess.DEVNULL,
            timeout=1,
        )
    except (subprocess.SubprocessError, OSError):
        return ""
    text = raw.decode("utf-8", errors="replace").strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _wnck_windows() -> dict[str, Any]:
    import clippy_xfce.gi_setup  # noqa: F401
    import gi

    gi.require_version("Wnck", "3.0")
    from gi.repository import Wnck

    screen = Wnck.Screen.get_default()
    if screen is None:
        return {}
    screen.force_update()
    active = screen.get_active_window()
    workspace = screen.get_active_workspace()
    windows = []
    for window in screen.get_windows():
        if window.is_skip_tasklist() or window.is_skip_pager():
            continue
        windows.append(
            {
                "name": window.get_name() or "",
                "app": (window.get_class_instance_name() or window.get_class_group_name() or ""),
                "active": bool(active and window == active),
            }
        )
    return {
        "workspace": workspace.get_name() if workspace else "",
        "windows": windows[:24],
        "active": (active.get_name() if active else ""),
    }


def desktop_snapshot() -> dict[str, Any]:
    info: dict[str, Any] = {
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "XFCE"),
        "time": dt.datetime.now().strftime("%A %Y-%m-%d %H:%M"),
        "home": str(os.path.expanduser("~")),
        "cwd": os.getcwd(),
        "clipboard": clipboard_text(),
        "windows": [],
        "active": "",
        "workspace": "",
    }
    try:
        extra = run_on_ui(_wnck_windows, timeout=2.0)
        info.update(extra or {})
    except Exception:
        pass
    return info


def context_text(snapshot: dict[str, Any] | None = None) -> str:
    snap = snapshot or desktop_snapshot()
    lines = [
        f"User: {snap.get('user')}@{snap.get('host')}",
        f"OS: {snap.get('os')} ({snap.get('desktop')})",
        f"Time: {snap.get('time')}",
        f"Home: {snap.get('home')}",
        f"Workspace: {snap.get('workspace') or '(unknown)'}",
        f"Active window: {snap.get('active') or '(none)'}",
        "Open windows:",
    ]
    windows = snap.get("windows") or []
    if windows:
        for window in windows:
            mark = "*" if window.get("active") else "-"
            app = f" [{window.get('app')}]" if window.get("app") else ""
            lines.append(f"  {mark} {window.get('name')}{app}")
    else:
        lines.append("  (unavailable)")
    clip = snap.get("clipboard") or ""
    lines.append("Clipboard: " + (clip.replace("\n", " ") if clip else "(empty)"))
    return "\n".join(lines)
