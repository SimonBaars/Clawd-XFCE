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
        self._inside = False

    def acquire(self) -> bool:
        if self.bound:
            return True
        self.bound = bind_hotkey(self.accel, self._invoke)
        return self.bound

    def _invoke(self) -> None:
        self._inside = True
        try:
            self.callback()
        finally:
            self._inside = False

    def release(self) -> None:
        if not self.bound:
            return
        # libkeybinder segfaults if unbound from inside its own callback.
        if self._inside:
            self.bound = False
            import clippy_xfce.gi_setup  # noqa: F401
            from gi.repository import GLib

            GLib.idle_add(self._unbind)
            return
        self._unbind()

    def _unbind(self) -> bool:
        unbind_hotkey(self.accel)
        self.bound = False
        return False


class EscapeWatch:
    """See Escape even when Clippy's windows are hidden (XQueryKeymap)."""

    def __init__(self, callback: Callable[[], None], armed: Callable[[], bool] | None = None) -> None:
        self.callback = callback
        self.armed = armed or (lambda: True)
        self._timer = 0
        self._down = False
        self._display = None
        self._keycode = 0

    def start(self) -> None:
        if self._timer:
            return
        self._open()
        # Ignore a key that is already held, so arming the watch does not
        # look like a fresh press.
        self._down = self.query_down()
        import clippy_xfce.gi_setup  # noqa: F401
        from gi.repository import GLib

        # A human tap is short. Poll faster than the tap so it is not missed.
        # This does not grab the key, so the app Clawd is driving still receives it.
        self._timer = GLib.timeout_add(10, self._poll)

    def stop(self) -> None:
        if self._timer:
            import clippy_xfce.gi_setup  # noqa: F401
            from gi.repository import GLib

            GLib.source_remove(self._timer)
            self._timer = 0
        self._close()
        self._down = False

    def _open(self) -> None:
        try:
            from Xlib import XK, display

            self._display = display.Display()
            self._keycode = int(self._display.keysym_to_keycode(XK.string_to_keysym("Escape")))
        except Exception:
            self._display = None
            self._keycode = 0

    def _close(self) -> None:
        if self._display is None:
            return
        try:
            self._display.close()
        except Exception:
            pass
        self._display = None

    def query_down(self) -> bool:
        if self._display is None or not self._keycode:
            return False
        try:
            bits = self._display.query_keymap()
            return bool(bits[self._keycode // 8] & (1 << (self._keycode % 8)))
        except Exception:
            return False

    def _poll(self) -> bool:
        if not self.armed():
            self._down = False
            return True
        down = self.query_down()
        if down and not self._down:
            self._down = True
            self.callback()
        elif not down:
            self._down = False
        return True
