"""Keyboard-shortcut help for the speech bubble."""

from __future__ import annotations

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gtk


def pretty_accel(accel: str) -> str:
    text = (accel or "").strip()
    for src, dest in (
        ("<Primary>", "Ctrl+"),
        ("<Ctrl>", "Ctrl+"),
        ("<Control>", "Ctrl+"),
        ("<Alt>", "Alt+"),
        ("<Shift>", "Shift+"),
        ("<Super>", "Super+"),
        ("<Meta>", "Super+"),
    ):
        text = text.replace(src, dest)
    text = text.replace("<", "").replace(">", "")
    parts = [part for part in text.split("+") if part]
    if parts and len(parts[-1]) == 1 and parts[-1].isalpha():
        parts[-1] = parts[-1].upper()
    return "+".join(parts) or "Ctrl+Alt+C"


def shortcut_lines(hotkey: str, hold_key: str = "Shift", dodge: bool = False) -> list[tuple[str, str]]:
    rows = [
        (pretty_accel(hotkey), "Show the chat, or steer while working"),
        ("Escape", "Stop computer use, or hide the chat when idle"),
        ("Enter", "Send a message"),
        ("F1 or ?", "Open this shortcut list"),
        ("Click the mascot", "Show or hide the chat"),
        ("Drag the mascot", "Move it — the chat follows"),
        ("Right-click the mascot", "Open the menu"),
    ]
    if dodge:
        rows.append((f"Hold {hold_key}", "Keep the mascot still so you can click it"))
        rows.append(("Chat open", "The mascot stays put while the chat is open"))
    return rows


class ShortcutsDialog(Gtk.Dialog):
    def __init__(
        self,
        parent: Gtk.Window | None,
        hotkey: str,
        hold_key: str = "Shift",
        dodge: bool = False,
    ) -> None:
        super().__init__(title="Keyboard shortcuts", transient_for=parent, flags=0)
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        self.set_default_response(Gtk.ResponseType.CLOSE)
        self.set_keep_above(True)
        self.get_style_context().add_class("clippy-bubble")
        box = self.get_content_area()
        box.set_border_width(12)
        chrome = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        chrome.get_style_context().add_class("clippy-chrome")
        title = Gtk.Label(label="Keyboard shortcuts", xalign=0)
        title.get_style_context().add_class("clippy-title")
        chrome.pack_start(title, False, False, 0)
        grid = Gtk.Grid(column_spacing=16, row_spacing=6)
        for index, (key, action) in enumerate(shortcut_lines(hotkey, hold_key, dodge)):
            key_label = Gtk.Label(label=key, xalign=0)
            key_label.get_style_context().add_class("clippy-title")
            action_label = Gtk.Label(label=action, xalign=0)
            action_label.get_style_context().add_class("clippy-sub")
            grid.attach(key_label, 0, index, 1, 1)
            grid.attach(action_label, 1, index, 1, 1)
        chrome.pack_start(grid, False, False, 0)
        box.add(chrome)
        self.show_all()
        self.present()


def run_shortcuts(
    parent: Gtk.Window | None,
    hotkey: str,
    hold_key: str = "Shift",
    dodge: bool = False,
) -> None:
    dialog = ShortcutsDialog(parent, hotkey, hold_key, dodge)
    dialog.run()
    dialog.destroy()
