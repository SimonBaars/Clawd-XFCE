"""Short on-screen captions while the assistant is using the computer."""

from __future__ import annotations

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gdk, GLib, Gtk, Pango


def clamp_seconds(value: object) -> int:
    try:
        seconds = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        seconds = 5.0
    return max(2, min(12, int(round(seconds))))


def caption_text(text: str) -> str:
    return " ".join((text or "").split())[:400]


class FlashWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("clippy")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.set_app_paintable(True)
        self.get_style_context().add_class("clippy-bubble")
        self.stick()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        chrome = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        chrome.get_style_context().add_class("clippy-chrome")
        chrome.get_style_context().add_class("clippy-flash")
        self.who = Gtk.Label(label="Clippy", xalign=0)
        self.who.get_style_context().add_class("clippy-title")
        self.body = Gtk.Label(label="", xalign=0)
        self.body.set_line_wrap(True)
        self.body.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.body.set_max_width_chars(48)
        self.body.get_style_context().add_class("clippy-sub")
        chrome.pack_start(self.who, False, False, 0)
        chrome.pack_start(self.body, False, False, 0)
        self.add(chrome)
        self.connect("button-press-event", lambda *_: self.dismiss() or True)
        self._timer = 0
        self._mascot = "Clippy"

    def set_mascot_name(self, name: str) -> None:
        self._mascot = name or "Clippy"
        self.who.set_text(self._mascot)

    def show_message(self, text: str, seconds: object = 5) -> None:
        caption = caption_text(text)
        if not caption:
            return
        self.body.set_text(caption)
        self.show_all()
        GLib.idle_add(self._place)
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(clamp_seconds(seconds) * 1000, self._timeout)

    def dismiss(self) -> None:
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        self.hide()

    def _timeout(self) -> bool:
        self._timer = 0
        self.hide()
        return False

    def _place(self) -> bool:
        display = self.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        work = monitor.get_workarea()
        width = max(self.get_allocated_width(), self.get_size()[0])
        self.move(work.x + max(8, (work.width - width) // 2), work.y + 18)
        return False
