"""GTK CSS for the speech bubble and chrome."""

from __future__ import annotations

CSS = """
window.clippy-bubble {
  background-color: transparent;
}

.clippy-chrome {
  background-color: #fff4a8;
  border: 2px solid #1a1408;
  border-radius: 18px;
  padding: 10px;
}

.clippy-chrome,
.clippy-chrome label,
.clippy-chrome entry,
.clippy-chrome button,
.clippy-chrome textview {
  color: #1a1408;
}

.clippy-header {
  padding: 0 2px 6px 2px;
}

.clippy-title {
  font-weight: bold;
  font-size: 15px;
  color: #1a1408;
}

.clippy-sub {
  font-size: 11px;
  color: #4a3b1c;
}

.clippy-messages {
  background-color: #fffce8;
  border-radius: 10px;
  padding: 4px;
}

.clippy-msg {
  padding: 7px 9px;
  border-radius: 10px;
  margin: 3px 0;
}

.clippy-msg label {
  color: #1a1408;
}

.clippy-msg.user {
  background-color: #cfe6ff;
}

.clippy-msg.assistant {
  background-color: #ffe56a;
}

.clippy-msg.system {
  background-color: #eee2b0;
  font-style: italic;
}

.clippy-msg.error {
  background-color: #ffc4b8;
}

.clippy-msg.tool {
  background-color: #efe4b0;
  font-size: 11px;
}

.clippy-input {
  background-image: none;
  background-color: #fffef8;
  border: 1px solid #1a1408;
  border-radius: 8px;
  padding: 6px 8px;
  color: #1a1408;
  caret-color: #1a1408;
}

window.clippy-bubble button,
.clippy-button {
  background-image: none;
  background-color: #f3dc6a;
  border: 1px solid #1a1408;
  border-radius: 8px;
  padding: 3px 9px;
  color: #1a1408;
  min-height: 22px;
  box-shadow: none;
  text-shadow: none;
}

window.clippy-bubble button label,
.clippy-button label {
  color: #1a1408;
}

window.clippy-bubble button:hover,
.clippy-button:hover {
  background-image: none;
  background-color: #ffe45c;
}

window.clippy-bubble button.destructive,
.clippy-button.destructive {
  background-image: none;
  background-color: #f0b4a8;
}

.clippy-flash {
  padding: 8px 12px;
}

window.clippy-bubble entry {
  background-image: none;
  background-color: #fffef8;
  color: #1a1408;
  box-shadow: none;
  caret-color: #1a1408;
}
"""


def load_css() -> None:
    import clippy_xfce.gi_setup  # noqa: F401
    from gi.repository import Gdk, Gtk

    settings = Gtk.Settings.get_default()
    if settings is not None:
        settings.set_property("gtk-application-prefer-dark-theme", False)
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 200,
    )
