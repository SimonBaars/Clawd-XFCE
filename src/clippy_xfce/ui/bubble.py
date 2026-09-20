"""Classic speech-bubble chat window."""

from __future__ import annotations

from collections.abc import Callable

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gdk, GLib, Gtk, Pango


class BubbleWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_default_size(400, 460)
        self.set_app_paintable(True)
        self.get_style_context().add_class("clippy-bubble")
        self.stick()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.on_send: Callable[[str], None] | None = None
        self.on_stop: Callable[[], None] | None = None
        self.on_new: Callable[[], None] | None = None
        self.on_history: Callable[[], None] | None = None
        self.on_settings: Callable[[], None] | None = None
        self._hidden_for_shot = False
        self._was_visible = False

        shell = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        chrome = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        chrome.get_style_context().add_class("clippy-chrome")
        tail = Gtk.DrawingArea()
        tail.set_size_request(22, 90)
        tail.connect("draw", self._draw_tail)
        shell.pack_start(chrome, True, True, 0)
        shell.pack_start(tail, False, False, 0)
        self.add(shell)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.get_style_context().add_class("clippy-header")
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.title_label = Gtk.Label(label="Clippy", xalign=0)
        self.title_label.get_style_context().add_class("clippy-title")
        self.status_label = Gtk.Label(label="Ready to help.", xalign=0)
        self.status_label.get_style_context().add_class("clippy-sub")
        titles.pack_start(self.title_label, False, False, 0)
        titles.pack_start(self.status_label, False, False, 0)
        header.pack_start(titles, True, True, 0)
        self.new_btn = _btn("New", self._new)
        self.hist_btn = _btn("History", self._history)
        self.set_btn = _btn("Settings", self._settings)
        self.hide_btn = _btn("Hide", lambda *_: self.hide())
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for button in (self.new_btn, self.hist_btn, self.set_btn, self.hide_btn):
            buttons.pack_start(button, False, False, 0)
        header.pack_end(buttons, False, False, 0)
        chrome.pack_start(header, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.get_style_context().add_class("clippy-messages")
        scrolled.add(self.listbox)
        chrome.pack_start(scrolled, True, True, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("It looks like you're writing something…")
        self.entry.get_style_context().add_class("clippy-input")
        self.entry.connect("activate", self._send)
        self.send_btn = _btn("Ask", self._send)
        self.stop_btn = _btn("Stop", self._stop)
        self.stop_btn.get_style_context().add_class("destructive")
        self.stop_btn.set_sensitive(False)
        row.pack_start(self.entry, True, True, 0)
        row.pack_start(self.send_btn, False, False, 0)
        row.pack_start(self.stop_btn, False, False, 0)
        chrome.pack_start(row, False, False, 0)

        self.connect("button-press-event", self._drag)

    def set_busy(self, busy: bool, status: str | None = None) -> None:
        self.send_btn.set_sensitive(not busy)
        self.entry.set_sensitive(not busy)
        self.stop_btn.set_sensitive(busy)
        if status:
            self.status_label.set_text(status)
        elif busy:
            self.status_label.set_text("Working…")
        else:
            self.status_label.set_text("Ready to help.")

    def set_status(self, text: str) -> None:
        self.status_label.set_text(text)

    def focus_input(self) -> None:
        self.show_all()
        self.present()
        self.entry.grab_focus()

    def add_message(self, kind: str, text: str) -> None:
        label = Gtk.Label(label=text, xalign=0)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(42)
        label.set_selectable(True)
        box = Gtk.Box()
        box.get_style_context().add_class("clippy-msg")
        box.get_style_context().add_class(kind)
        box.pack_start(label, True, True, 0)
        row = Gtk.ListBoxRow()
        row.add(box)
        self.listbox.add(row)
        self.listbox.show_all()
        GLib.idle_add(self._scroll_end)

    def clear_messages(self) -> None:
        for child in list(self.listbox.get_children()):
            self.listbox.remove(child)

    def hide_for_capture(self) -> None:
        self._was_visible = self.get_visible()
        self._hidden_for_shot = True
        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

    def restore_after_capture(self) -> None:
        if self._hidden_for_shot and self._was_visible:
            self.show_all()
        self._hidden_for_shot = False

    def place_near(self, char: Gtk.Window) -> None:
        cx, cy = char.get_position()
        _cw, ch = char.get_size()
        bw, bh = self.get_size()
        display = self.get_display()
        monitor = display.get_monitor_at_window(char.get_window()) if char.get_window() else display.get_primary_monitor()
        work = monitor.get_workarea()
        x = cx - bw - 14
        if x < work.x + 8:
            x = cx + char.get_size()[0] + 14
        y = cy + ch - bh
        y = max(work.y + 8, min(y, work.y + work.height - bh - 8))
        x = max(work.x + 8, min(x, work.x + work.width - bw - 8))
        self.move(x, y)

    def _scroll_end(self) -> bool:
        adj = self.listbox.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())
        return False

    def _send(self, *_args) -> None:
        text = self.entry.get_text().strip()
        if not text or not self.on_send:
            return
        self.entry.set_text("")
        self.add_message("user", text)
        self.on_send(text)

    def _stop(self, *_args) -> None:
        if self.on_stop:
            self.on_stop()

    def _new(self, *_args) -> None:
        if self.on_new:
            self.on_new()

    def _history(self, *_args) -> None:
        if self.on_history:
            self.on_history()

    def _settings(self, *_args) -> None:
        if self.on_settings:
            self.on_settings()

    def _draw_tail(self, _area, ctx) -> bool:
        import cairo

        ctx.set_source_rgb(1.0, 0.957, 0.659)
        ctx.move_to(0, 28)
        ctx.line_to(20, 48)
        ctx.line_to(0, 68)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.03)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgb(1.0, 0.957, 0.659)
        ctx.rectangle(0, 30, 3, 36)
        ctx.fill()
        return True

    def _drag(self, _win, event) -> bool:
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            widget = self.get_focus()
            if isinstance(widget, Gtk.Entry):
                return False
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
        return False


def _btn(label: str, handler) -> Gtk.Button:
    button = Gtk.Button(label=label)
    button.get_style_context().add_class("clippy-button")
    button.connect("clicked", handler)
    return button
