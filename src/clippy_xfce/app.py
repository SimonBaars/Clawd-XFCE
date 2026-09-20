"""Gtk.Application that hosts Clippy on XFCE."""

from __future__ import annotations

import argparse
import sys
import threading

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gdk, Gio, GLib, Gtk

from clippy_xfce.agent.claude import AgentEvent, ClippyAgent
from clippy_xfce.agent.computer import ComputerUse, X11Computer
from clippy_xfce.agent.memory import MemoryStore
from clippy_xfce.agent.tools import ToolHub
from clippy_xfce.config import load_settings, save_settings
from clippy_xfce.desktop import install_desktop_files
from clippy_xfce.sounds import SoundPlayer
from clippy_xfce.sprites import ensure_assets
from clippy_xfce.ui.bubble import BubbleWindow
from clippy_xfce.ui.character import CharacterWindow
from clippy_xfce.ui.confirm import ActionGate
from clippy_xfce.ui.history import replay_visible, run_history
from clippy_xfce.ui.hotkey import bind_hotkey
from clippy_xfce.ui.settings import run_settings
from clippy_xfce.ui.theme import load_css
from clippy_xfce.ui.tray import TrayIcon


class ClippyApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="org.xfce.clippy", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.settings = load_settings()
        self.store = MemoryStore()
        self.character: CharacterWindow | None = None
        self.bubble: BubbleWindow | None = None
        self.agent: ClippyAgent | None = None
        self.gate: ActionGate | None = None
        self._worker: threading.Thread | None = None
        self.ask_on_start = False
        self.pending_say = ""

    def do_command_line(self, command_line):  # noqa: N802
        parser = argparse.ArgumentParser(prog="clippy")
        parser.add_argument("--ask", action="store_true", help="Open the speech bubble")
        parser.add_argument("--new", action="store_true", help="Start a new conversation")
        parser.add_argument("--say", default="", help="Send a message to the running Clippy")
        parser.add_argument("--quit", action="store_true", help="Quit a running Clippy")
        args, _unknown = parser.parse_known_args(command_line.get_arguments()[1:])
        if args.quit:
            if self.character:
                self.quit()
            return 0
        self.ask_on_start = args.ask or bool(args.say)
        self.pending_say = args.say
        self.activate()
        if args.new and self.agent:
            self._new_chat()
        if args.ask and self.bubble:
            self.show_bubble()
        if args.say and self.agent and self.bubble:
            self.show_bubble()
            self.bubble.add_message("user", args.say)
            self._ask(args.say)
        return 0

    def do_activate(self) -> None:  # noqa: N802
        if self.character:
            self.character.present()
            if self.ask_on_start:
                self.show_bubble()
            return
        from clippy_xfce.gtkutil import set_ui_active

        set_ui_active(True)
        load_css()
        if not self.settings.api_key:
            updated = run_settings(None, self.settings)
            if updated:
                self.settings = updated
                save_settings(self.settings)
        if self.settings.api_key:
            import os

            os.environ.setdefault("ANTHROPIC_API_KEY", self.settings.api_key)

        agent_def, frames, _sounds = ensure_assets()
        sounds = SoundPlayer(enabled=self.settings.sounds)
        sounds.prepare()
        install_desktop_files(self.settings.autostart)

        self.character = CharacterWindow(
            agent_def,
            frames,
            self.settings.scale,
            sounds,
            idle_seconds=self.settings.idle_seconds,
        )
        self.character.set_application(self)
        self.character.on_click = self.toggle_bubble
        self.character.on_menu = self._fill_menu
        self.character.on_moved = self._place_bubble
        self.character.place_default()
        self.character.show_all()
        GLib.idle_add(self.character._update_shape)

        self.bubble = BubbleWindow()
        self.bubble.set_application(self)
        self.bubble.on_send = self._ask
        self.bubble.on_stop = self._stop
        self.bubble.on_new = self._new_chat
        self.bubble.on_history = self._history
        self.bubble.on_settings = self._settings

        self.gate = ActionGate(lambda: self.bubble, self.settings.confirm_mode)
        computer = ComputerUse(
            X11Computer(),
            max_edge=self.settings.max_screenshot_edge,
            before_shot=self._hide_for_shot if self.settings.hide_self_in_screenshots else None,
            after_shot=self._show_after_shot if self.settings.hide_self_in_screenshots else None,
        )
        hub = ToolHub(self.store, express=self._express)
        self.agent = ClippyAgent(
            self.settings,
            self.store,
            computer,
            hub,
            emit=self._on_event,
            confirm=self.gate.decide,
        )
        self.agent.new_conversation()

        TrayIcon(self.show_bubble, self.toggle_visible, self._history, self._settings, self.quit)
        bind_hotkey(self.settings.hotkey, self.show_bubble)

        if self.settings.proactive_greeting:
            self.character.play("Greeting", interrupt=True)
            self.bubble.add_message(
                "assistant",
                "Hi! I'm Clippy. I can see this XFCE desktop and help you get things done.",
            )
            self.show_bubble()
        elif self.ask_on_start:
            self.show_bubble()

    def _hide_for_shot(self) -> None:
        if self.character:
            self.character.hide_for_capture()
        if self.bubble:
            self.bubble.hide_for_capture()

    def _show_after_shot(self) -> None:
        if self.character:
            self.character.restore_after_capture()
        if self.bubble:
            self.bubble.restore_after_capture()

    def _express(self, mood: str, animation: str | None) -> str:
        def go() -> str:
            assert self.character is not None
            if animation:
                self.character.play(animation, interrupt=True)
                return animation
            return self.character.play_mood(mood, interrupt=True)

        from clippy_xfce.gtkutil import run_on_ui

        return run_on_ui(go)

    def _fill_menu(self, menu: Gtk.Menu) -> None:
        items = [
            ("Ask Clippy", self.show_bubble),
            ("New chat", self._new_chat),
            ("History", self._history),
            ("Settings", self._settings),
            ("Hide", self.toggle_visible),
            ("Quit", self.quit),
        ]
        for label, handler in items:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda _i, cb=handler: cb())
            menu.append(item)

    def show_bubble(self) -> None:
        if not self.bubble or not self.character:
            return
        self.bubble.show_all()
        self._place_bubble()
        self.bubble.focus_input()
        self.character.play_mood("talk")

    def toggle_bubble(self) -> None:
        if not self.bubble:
            return
        if self.bubble.get_visible():
            self.bubble.hide()
        else:
            self.show_bubble()

    def toggle_visible(self) -> None:
        if not self.character:
            return
        if self.character.get_visible():
            self.character.hide()
            if self.bubble:
                self.bubble.hide()
        else:
            self.character.show_all()
            self.show_bubble()

    def _place_bubble(self) -> None:
        if self.bubble and self.character and self.bubble.get_visible():
            self.bubble.place_near(self.character)

    def _ask(self, text: str) -> None:
        if not self.agent or not self.bubble:
            return
        if self._worker and self._worker.is_alive():
            self.bubble.add_message("system", "I'm still working on the last thing.")
            return
        if not self.settings.api_key:
            self.bubble.add_message("error", "Add an Anthropic API key in Settings first.")
            self._settings()
            return
        self.gate.reset_turn() if self.gate else None
        self.bubble.set_busy(True, "Looking at your desktop…")
        if self.character:
            self.character.play_mood("think", interrupt=True)

        def work() -> None:
            try:
                self.agent.ask(text)
            except Exception as exc:
                GLib.idle_add(self.bubble.add_message, "error", str(exc))
            finally:
                GLib.idle_add(self.bubble.set_busy, False, "Ready to help.")
                GLib.idle_add(self.character.play_mood, "success")

        self._worker = threading.Thread(target=work, name="clippy-agent", daemon=True)
        self._worker.start()

    def _stop(self) -> None:
        if self.agent:
            self.agent.stop()
        if self.bubble:
            self.bubble.set_status("Stopping…")

    def _new_chat(self) -> None:
        if self.agent:
            self.agent.new_conversation()
        if self.bubble:
            self.bubble.clear_messages()
            self.bubble.add_message("system", "New conversation. I still remember earlier chats.")
            self.bubble.set_status("New chat")
        if self.character:
            self.character.play("Wave", interrupt=True)

    def _history(self) -> None:
        chosen = run_history(self.bubble, self.store)
        if chosen and self.agent and self.bubble:
            self.agent.load_conversation(chosen)
            self.bubble.clear_messages()
            replay_visible(self.store, chosen, self.bubble.add_message)
            self.show_bubble()

    def _settings(self) -> None:
        updated = run_settings(self.bubble, self.settings)
        if not updated:
            return
        self.settings = updated
        save_settings(self.settings)
        install_desktop_files(self.settings.autostart)
        if self.agent:
            self.agent.settings = self.settings
            self.agent.tool_mode = self.settings.tool_mode
        if self.gate:
            self.gate.mode = self.settings.confirm_mode
        if self.character:
            self.character.sounds.enabled = self.settings.sounds
            self.character.scale = self.settings.scale
            self.character._show_frame()
        if self.bubble:
            self.bubble.add_message("system", "Settings saved.")

    def _on_event(self, event: AgentEvent) -> None:
        def ui() -> bool:
            if not self.bubble or not self.character:
                return False
            if event.kind == "assistant":
                self.bubble.add_message("assistant", event.text)
                self.character.play_mood("talk")
            elif event.kind == "tool":
                self.bubble.add_message("tool", event.text)
                self.bubble.set_status(event.text[:60])
                self.character.play_mood("act")
            elif event.kind == "tool_error":
                self.bubble.add_message("error", event.text)
                self.character.play_mood("error", interrupt=True)
            elif event.kind == "error":
                self.bubble.add_message("error", event.text)
                self.character.play_mood("error", interrupt=True)
            elif event.kind == "warn":
                self.bubble.add_message("system", event.text)
            elif event.kind == "status":
                self.bubble.set_status(event.text)
            elif event.kind == "stopped":
                self.bubble.add_message("system", event.text)
            return False

        GLib.idle_add(ui)


def main(argv: list[str] | None = None) -> int:
    Gdk.set_program_class("Clippy")
    app = ClippyApp()
    return app.run(argv or sys.argv)
