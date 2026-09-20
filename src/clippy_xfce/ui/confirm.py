"""Ask the user before Clippy acts."""

from __future__ import annotations

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gtk


def confirm_action(parent: Gtk.Window | None, summary: str, destructive: bool) -> str:
    """Return allow, allow_all, or deny."""
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.WARNING if destructive else Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text="Clippy wants to do something",
    )
    dialog.format_secondary_text(summary)
    dialog.add_button("Deny", Gtk.ResponseType.NO)
    dialog.add_button("Allow this turn", Gtk.ResponseType.APPLY)
    dialog.add_button("Allow", Gtk.ResponseType.YES)
    dialog.set_default_response(Gtk.ResponseType.YES if not destructive else Gtk.ResponseType.NO)
    response = dialog.run()
    dialog.destroy()
    if response == Gtk.ResponseType.YES:
        return "allow"
    if response == Gtk.ResponseType.APPLY:
        return "allow_all"
    return "deny"


class ActionGate:
    def __init__(self, parent_fn, mode: str) -> None:
        self.parent_fn = parent_fn
        self.mode = mode
        self.allow_all = False

    def reset_turn(self) -> None:
        self.allow_all = False

    def decide(self, summary: str, destructive: bool) -> bool:
        if self.mode == "never":
            return True
        if self.mode == "destructive" and not destructive:
            return True
        if self.allow_all:
            return True
        from clippy_xfce.gtkutil import run_on_ui

        answer = run_on_ui(lambda: confirm_action(self.parent_fn(), summary, destructive))
        if answer == "allow_all":
            self.allow_all = True
            return True
        return answer == "allow"
