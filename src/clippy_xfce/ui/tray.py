"""Ayatana / AppIndicator tray icon."""

from __future__ import annotations

from collections.abc import Callable

import clippy_xfce.gi_setup  # noqa: F401
import gi

from clippy_xfce.paths import icon_path


class TrayIcon:
    def __init__(
        self,
        on_ask: Callable[[], None],
        on_toggle: Callable[[], None],
        on_stop: Callable[[], None],
        on_pause: Callable[[], None],
        on_history: Callable[[], None],
        on_settings: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.indicator = None
        menu = _menu(on_ask, on_toggle, on_stop, on_pause, on_history, on_settings, on_quit)
        icon = str(icon_path())
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AppIndicator
        except Exception:
            try:
                gi.require_version("AppIndicator3", "0.1")
                from gi.repository import AppIndicator3 as AppIndicator
            except Exception:
                self._status_icon(icon, menu)
                return
        self.indicator = AppIndicator.Indicator.new(
            "clippy-xfce",
            icon,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Clippy")
        self.indicator.set_menu(menu)

    def _status_icon(self, icon: str, menu) -> None:
        from gi.repository import Gtk

        status = Gtk.StatusIcon.new_from_file(icon)
        status.set_tooltip_text("Clippy")
        status.connect("activate", lambda *_: menu.get_children()[0].activate())
        status.connect("popup-menu", lambda icon, button, time: menu.popup(None, None, None, None, button, time))
        self.indicator = status


def _menu(on_ask, on_toggle, on_stop, on_pause, on_history, on_settings, on_quit):
    from gi.repository import Gtk

    menu = Gtk.Menu()
    items = [
        ("Ask Clippy", on_ask),
        ("Stop", on_stop),
        ("Pause computer use", on_pause),
        ("Show / Hide", on_toggle),
        ("History", on_history),
        ("Settings", on_settings),
        ("Quit", on_quit),
    ]
    for label, handler in items:
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda _item, cb=handler: cb())
        menu.append(item)
    menu.show_all()
    return menu
