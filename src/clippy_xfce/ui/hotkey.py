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


class HeldHotkey:
    """Bind a global accel for the duration of a session, once."""

    def __init__(self, accel: str, callback: Callable[[], None]) -> None:
        self.accel = accel
        self.callback = callback
        self.bound = False

    def acquire(self) -> bool:
        if self.bound:
            return True
        self.bound = bind_hotkey(self.accel, self.callback)
        return self.bound

    def release(self) -> None:
        if not self.bound:
            return
        unbind_hotkey(self.accel)
        self.bound = False
