"""Conversation history dialog."""

from __future__ import annotations

from collections.abc import Callable

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gtk

from clippy_xfce.agent.memory import Conversation, MemoryStore, first_text


class HistoryDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window | None, store: MemoryStore) -> None:
        super().__init__(title="Clippy conversations", transient_for=parent, flags=0)
        self.store = store
        self.chosen: int | None = None
        self.add_buttons(
            "Delete",
            Gtk.ResponseType.REJECT,
            "Open",
            Gtk.ResponseType.OK,
            Gtk.STOCK_CLOSE,
            Gtk.ResponseType.CLOSE,
        )
        self.set_default_size(520, 380)
        self.listbox = Gtk.ListBox()
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.listbox)
        self.get_content_area().pack_start(scrolled, True, True, 0)
        self._rows: dict[Gtk.ListBoxRow, Conversation] = {}
        self.refresh()
        self.show_all()

    def refresh(self) -> None:
        for child in list(self.listbox.get_children()):
            self.listbox.remove(child)
        self._rows.clear()
        for convo in self.store.list_conversations():
            label = Gtk.Label(label=f"{convo.title}\n{convo.summary[:120]}", xalign=0)
            label.set_line_wrap(True)
            row = Gtk.ListBoxRow()
            row.add(label)
            self.listbox.add(row)
            self._rows[row] = convo
        self.listbox.show_all()

    def selected(self) -> Conversation | None:
        row = self.listbox.get_selected_row()
        return self._rows.get(row) if row else None


def run_history(parent: Gtk.Window | None, store: MemoryStore) -> int | None:
    dialog = HistoryDialog(parent, store)
    chosen = None
    while True:
        response = dialog.run()
        convo = dialog.selected()
        if response == Gtk.ResponseType.OK and convo:
            chosen = convo.id
            break
        if response == Gtk.ResponseType.REJECT and convo:
            store.delete_conversation(convo.id)
            dialog.refresh()
            continue
        break
    dialog.destroy()
    return chosen


def replay_visible(store: MemoryStore, conversation_id: int, add: Callable[[str, str], None]) -> None:
    for message in store.messages(conversation_id):
        text = first_text(message.get("content"))
        if not text:
            continue
        kind = "user" if message.get("role") == "user" else "assistant"
        if text.startswith("Desktop now:"):
            continue
        add(kind, text)
