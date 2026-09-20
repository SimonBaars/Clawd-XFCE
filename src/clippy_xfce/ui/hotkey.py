"""Global XFCE hotkey via libkeybinder."""

from __future__ import annotations

from collections.abc import Callable


def bind_hotkey(accel: str, callback: Callable[[], None]) -> bool:
    try:
        import gi

        gi.require_version("Keybinder", "3.0")
        from gi.repository import Keybinder

        Keybinder.init()
        return bool(Keybinder.bind(accel, lambda *_: callback()))
    except Exception:
        return False


def unbind_hotkey(accel: str) -> None:
    try:
        import gi

        gi.require_version("Keybinder", "3.0")
        from gi.repository import Keybinder

        Keybinder.unbind(accel)
    except Exception:
        pass
