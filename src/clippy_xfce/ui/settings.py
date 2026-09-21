"""Settings dialog."""

from __future__ import annotations

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gtk

from clippy_xfce.config import CONFIRM_MODES, MODELS, SCREENSHOT_MODES, TOOL_MODES, Settings
from clippy_xfce.dodge import HOLD_KEYS
from clippy_xfce.mascots import MASCOTS


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window | None, settings: Settings) -> None:
        super().__init__(title="Clippy settings", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        self.set_default_size(460, 420)
        self.get_style_context().add_class("clippy-bubble")
        self.settings = settings
        box = self.get_content_area()
        box.set_border_width(10)
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        box.add(grid)

        self.api = Gtk.Entry()
        self.api.set_visibility(False)
        self.api.set_text(settings.api_key)
        self.api.set_placeholder_text("sk-ant-…")

        self.model = Gtk.ComboBoxText()
        for model in MODELS:
            self.model.append_text(model)
        self.model.set_active(max(0, MODELS.index(settings.model) if settings.model in MODELS else 0))

        self.tool_mode = Gtk.ComboBoxText()
        for mode in TOOL_MODES:
            self.tool_mode.append_text(mode)
        self.tool_mode.set_active(TOOL_MODES.index(settings.tool_mode) if settings.tool_mode in TOOL_MODES else 0)

        self.confirm = Gtk.ComboBoxText()
        for mode in CONFIRM_MODES:
            self.confirm.append_text(mode)
        self.confirm.set_active(CONFIRM_MODES.index(settings.confirm_mode))

        self.shots = Gtk.ComboBoxText()
        for mode in SCREENSHOT_MODES:
            self.shots.append_text(mode)
        self.shots.set_active(SCREENSHOT_MODES.index(settings.screenshot_mode))

        self.computer = Gtk.CheckButton(label="Allow Claude to use the computer")
        self.computer.set_active(settings.computer_use)
        self.bash = Gtk.CheckButton(label="Allow terminal and bash (run commands, type in terminals)")
        self.bash.set_active(settings.bash_tool)
        self.editor = Gtk.CheckButton(label="Allow text editor")
        self.editor.set_active(settings.editor_tool)
        self.sounds = Gtk.CheckButton(label="Play Clippy sounds")
        self.sounds.set_active(settings.sounds)
        self.hide_self = Gtk.CheckButton(label="Hide Clippy in screenshots")
        self.hide_self.set_active(settings.hide_self_in_screenshots)
        self.greet = Gtk.CheckButton(label="Greet on startup")
        self.greet.set_active(settings.proactive_greeting)
        self.autostart = Gtk.CheckButton(label="Start Clippy when I log in")
        self.autostart.set_active(settings.autostart)
        self.dodge = Gtk.CheckButton(label="Skitter away from the mouse")
        self.dodge.set_active(settings.dodge_mouse)

        self.dodge_hold = Gtk.ComboBoxText()
        for key in HOLD_KEYS:
            self.dodge_hold.append_text(key)
        hold = settings.dodge_hold_key if settings.dodge_hold_key in HOLD_KEYS else "Shift"
        self.dodge_hold.set_active(HOLD_KEYS.index(hold))

        self.scale = Gtk.SpinButton.new_with_range(0.75, 6.0, 0.25)
        self.scale.set_value(settings.scale)
        self.tokens = Gtk.SpinButton.new_with_range(256, 16000, 256)
        self.tokens.set_value(settings.max_tokens)
        self.iters = Gtk.SpinButton.new_with_range(0, 500, 1)
        self.iters.set_value(settings.max_iterations)
        self.iters.set_tooltip_text("0 means keep going until it finishes or you press Escape")
        self.hotkey = Gtk.Entry()
        self.hotkey.set_text(settings.hotkey)
        self.mascot = Gtk.ComboBoxText()
        for key, label in MASCOTS:
            self.mascot.append(key, label)
        if settings.mascot in dict(MASCOTS):
            self.mascot.set_active_id(settings.mascot)
        else:
            self.mascot.set_active(0)

        rows = [
            ("API key", self.api),
            ("Model", self.model),
            ("Computer-use API", self.tool_mode),
            ("Confirm actions", self.confirm),
            ("Attach screenshots", self.shots),
            ("Mascot", self.mascot),
            ("Hotkey", self.hotkey),
            ("Hold to keep still", self.dodge_hold),
            ("Mascot size", self.scale),
            ("Max tokens", self.tokens),
            ("Max steps (0 = none)", self.iters),
        ]
        for index, (label, widget) in enumerate(rows):
            grid.attach(Gtk.Label(label=label, xalign=0), 0, index, 1, 1)
            grid.attach(widget, 1, index, 1, 1)
        checks = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for widget in (
            self.computer,
            self.bash,
            self.editor,
            self.sounds,
            self.hide_self,
            self.greet,
            self.autostart,
            self.dodge,
        ):
            checks.pack_start(widget, False, False, 0)
        grid.attach(checks, 0, len(rows), 2, 1)
        self.show_all()

    def result_settings(self) -> Settings:
        data = Settings(
            model=self.model.get_active_text() or self.settings.model,
            max_tokens=int(self.tokens.get_value()),
            max_iterations=int(self.iters.get_value()),
            computer_use=self.computer.get_active(),
            bash_tool=self.bash.get_active(),
            editor_tool=self.editor.get_active(),
            tool_mode=self.tool_mode.get_active_text() or "toolset",
            confirm_mode=self.confirm.get_active_text() or "destructive",
            screenshot_mode=self.shots.get_active_text() or "always",
            hide_self_in_screenshots=self.hide_self.get_active(),
            sounds=self.sounds.get_active(),
            scale=float(self.scale.get_value()),
            pos_x=self.settings.pos_x,
            pos_y=self.settings.pos_y,
            start_hidden=self.settings.start_hidden,
            autostart=self.autostart.get_active(),
            proactive_greeting=self.greet.get_active(),
            max_screenshot_edge=self.settings.max_screenshot_edge,
            keep_screenshots=self.settings.keep_screenshots,
            idle_seconds=self.settings.idle_seconds,
            hotkey=self.hotkey.get_text().strip() or "<Ctrl><Alt>c",
            mascot=self.mascot.get_active_id() or self.settings.mascot,
            dodge_mouse=self.dodge.get_active(),
            dodge_hold_key=self.dodge_hold.get_active_text() or "Shift",
            config_version=self.settings.config_version,
            api_key=self.api.get_text().strip(),
        )
        return data.sanitized()


def run_settings(parent: Gtk.Window | None, settings: Settings) -> Settings | None:
    dialog = SettingsDialog(parent, settings)
    response = dialog.run()
    result = dialog.result_settings() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return result
