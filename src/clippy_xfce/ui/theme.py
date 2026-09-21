"""GTK CSS for the speech bubble — warm cream paper and Clawd terracotta."""

from __future__ import annotations

# RGB 0–1 for Cairo (bubble body, tail, accent)
CHROME_RGB = (0.957, 0.906, 0.859)  # #f4e7db
BORDER_RGB = (0.753, 0.510, 0.420)  # #c0826b
INK_RGB = (0.227, 0.165, 0.141)  # #3a2a24
ACCENT_RGB = (0.827, 0.451, 0.333)  # #d37355
SHADOW_RGB = (0.145, 0.090, 0.070)

CSS = """
window.clippy-bubble {
  background-color: transparent;
}

.clippy-chrome {
  background-color: transparent;
  border: none;
  border-radius: 0;
  padding: 4px 2px 2px 2px;
}

.clippy-card {
  background-color: #f4e7db;
  border: 1px solid #c0826b;
  border-radius: 18px;
  padding: 12px 14px;
}

.clippy-chrome,
.clippy-chrome label,
.clippy-chrome entry,
.clippy-chrome button,
.clippy-chrome textview,
dialog.clippy-bubble,
dialog.clippy-bubble label {
  color: #3a2a24;
  font-family: Cantarell, "Source Sans 3", "Adwaita Sans", "DejaVu Sans", sans-serif;
}

.clippy-header {
  padding: 0 2px 10px 2px;
  border-bottom: 1px solid #e2c8b8;
  margin-bottom: 2px;
}

.clippy-title {
  font-weight: 700;
  font-size: 17px;
  color: #b45338;
  letter-spacing: 0.2px;
}

.clippy-sub {
  font-size: 11px;
  color: #8d7166;
}

.clippy-messages {
  background-color: #f7ece4;
  border: 1px solid #e6cfc2;
  border-radius: 16px;
  padding: 8px 6px;
}

scrolledwindow {
  background-color: transparent;
  border: none;
  box-shadow: none;
}

list.clippy-messages,
list.clippy-messages row {
  background-color: transparent;
  background-image: none;
  border: none;
  box-shadow: none;
  outline: none;
  padding: 1px 2px;
}

list.clippy-messages row:hover,
list.clippy-messages row:selected,
list.clippy-messages row:selected:hover,
list.clippy-messages row:focus {
  background-color: transparent;
  background-image: none;
  box-shadow: none;
  outline: none;
}

.clippy-msg {
  padding: 8px 12px;
  border-radius: 16px;
  margin: 3px 2px;
}

.clippy-msg label {
  color: #3a2a24;
  font-size: 13px;
}

.clippy-msg.user {
  background-color: #fff8f2;
  border: 1px solid #e5d0c3;
  border-bottom-right-radius: 5px;
}

.clippy-msg.assistant {
  background-color: #efc4b4;
  border: 1px solid #e0a892;
  border-bottom-left-radius: 5px;
}

.clippy-msg.system {
  background-color: transparent;
  border: none;
  font-style: italic;
  padding: 2px 8px;
}

.clippy-msg.system label {
  color: #8d7166;
  font-size: 11px;
}

.clippy-msg.error {
  background-color: #f3d0c8;
  border: 1px solid #e0a898;
}

.clippy-msg.tool {
  background-color: transparent;
  border: none;
  padding: 1px 8px;
}

.clippy-msg.tool label {
  color: #9a7d70;
  font-size: 11px;
}

.clippy-composer {
  padding-top: 8px;
}

.clippy-input,
window.clippy-bubble entry,
dialog.clippy-bubble entry {
  background-image: none;
  background-color: #fff7f1;
  border: 1px solid #e4d0c4;
  border-radius: 16px;
  padding: 8px 12px;
  color: #3a2a24;
  caret-color: #d37355;
  box-shadow: none;
  min-height: 30px;
}

window.clippy-bubble entry:focus,
.clippy-input:focus,
dialog.clippy-bubble entry:focus {
  border-color: #d37355;
  background-color: #ffffff;
}

window.clippy-bubble entry selection,
.clippy-input selection,
.clippy-chrome label selection {
  background-color: #f4d4c8;
  color: #3a2a24;
}

window.clippy-bubble button,
.clippy-button,
dialog.clippy-bubble button {
  background-image: none;
  background-color: #f0e0d4;
  border: 1px solid #e4d0c4;
  border-radius: 12px;
  padding: 4px 10px;
  color: #3a2a24;
  min-height: 26px;
  box-shadow: none;
  text-shadow: none;
  -gtk-icon-shadow: none;
  outline: none;
}

window.clippy-bubble button:focus,
.clippy-button:focus,
dialog.clippy-bubble button:focus {
  outline: none;
  box-shadow: none;
  border-color: #d2ac9c;
}

window.clippy-bubble button label,
.clippy-button label,
dialog.clippy-bubble button label {
  color: #3a2a24;
  font-weight: 600;
}

window.clippy-bubble button:hover,
.clippy-button:hover,
dialog.clippy-bubble button:hover {
  background-image: none;
  background-color: #e8d0c2;
  border-color: #d2ac9c;
}

window.clippy-bubble button:active,
.clippy-button:active,
dialog.clippy-bubble button:active {
  background-image: none;
  background-color: #dfc0ae;
}

window.clippy-bubble button.clippy-text-btn {
  background-color: transparent;
  background-image: none;
  border: none;
  border-radius: 8px;
  min-height: 22px;
  padding: 2px 7px;
  color: #b45338;
}

window.clippy-bubble button.clippy-text-btn label {
  color: #b45338;
  font-weight: 600;
  font-size: 12px;
}

window.clippy-bubble button.clippy-text-btn:hover {
  background-color: #efd4c6;
  border: none;
}

window.clippy-bubble button.clippy-icon-btn {
  min-width: 28px;
  min-height: 28px;
  padding: 3px;
  border-radius: 14px;
  background-color: #efd8cc;
  border: 1px solid #e2c0b0;
  color: #8d7166;
}

window.clippy-bubble button.clippy-icon-btn:hover {
  background-color: #e8c8b8;
  border-color: #c0826b;
  color: #3a2a24;
}

window.clippy-bubble button.clippy-ask,
.clippy-button.clippy-ask {
  background-image: none;
  background: #d37355;
  background-color: #d37355;
  border-color: #c46245;
  border-radius: 14px;
  padding: 6px 14px;
  min-width: 58px;
}

window.clippy-bubble button.clippy-ask label,
.clippy-button.clippy-ask label {
  color: #fffaf6;
  font-weight: 700;
}

window.clippy-bubble button.clippy-ask:hover,
.clippy-button.clippy-ask:hover {
  background-color: #c46245;
  border-color: #b85a40;
}

window.clippy-bubble button.clippy-ask:active,
.clippy-button.clippy-ask:active {
  background-color: #b85a40;
}

window.clippy-bubble button.destructive,
.clippy-button.destructive {
  background-image: none;
  background-color: #f0d2c6;
  border-color: #d9a08c;
  color: #b45338;
}

window.clippy-bubble button.destructive label,
.clippy-button.destructive label {
  color: #b85a40;
}

window.clippy-bubble button.destructive:hover,
.clippy-button.destructive:hover {
  background-color: #f4d4c8;
}

window.clippy-bubble button:disabled,
.clippy-button:disabled {
  opacity: 0.42;
}

.clippy-key {
  background-color: #f8ebe3;
  border: 1px solid #e0b8a6;
  border-radius: 8px;
  padding: 3px 8px;
}

.clippy-key label {
  font-weight: 700;
  font-size: 12px;
  color: #b45338;
}

.clippy-flash {
  padding: 10px 16px;
}

scrollbar,
scrollbar slider {
  background-color: transparent;
  border: none;
  min-width: 7px;
}

scrollbar slider {
  background-color: #e4d0c4;
  border-radius: 8px;
  min-width: 7px;
}

scrollbar slider:hover {
  background-color: #d2ac9c;
}

dialog.clippy-bubble {
  background-color: #f4e7db;
}

dialog.clippy-bubble button {
  background-image: none;
  background-color: #f0e0d4;
  border: 1px solid #e4d0c4;
  border-radius: 11px;
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
