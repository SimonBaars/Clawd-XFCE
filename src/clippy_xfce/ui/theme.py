"""GTK CSS for the speech bubble — warm dark chrome and Clawd terracotta."""

from __future__ import annotations

# RGB 0–1 for Cairo (bubble body, tail, accent)
CHROME_RGB = (0.145, 0.122, 0.110)  # #25201c
BORDER_RGB = (0.690, 0.400, 0.318)  # #b06651
INK_RGB = (0.933, 0.890, 0.855)  # #eee3da
ACCENT_RGB = (0.827, 0.451, 0.333)  # #d37355
SHADOW_RGB = (0.02, 0.01, 0.01)

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
  background-color: #25201c;
  border: 1px solid #b06651;
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
  color: #eee3da;
  font-family: Cantarell, "Source Sans 3", "Adwaita Sans", "DejaVu Sans", sans-serif;
}

.clippy-header {
  padding: 0 2px 10px 2px;
  border-bottom: 1px solid #3d332e;
  margin-bottom: 2px;
}

.clippy-title {
  font-weight: 700;
  font-size: 17px;
  color: #e08a6e;
  letter-spacing: 0.2px;
}

.clippy-sub {
  font-size: 11px;
  color: #b39a8e;
}

.clippy-messages {
  background-color: #1b1715;
  border: 1px solid #3d332e;
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
  color: #eee3da;
  font-size: 13px;
}

.clippy-msg.user {
  background-color: #3a332f;
  border: 1px solid #544840;
  border-bottom-right-radius: 5px;
}

.clippy-msg.assistant {
  background-color: #6b3d32;
  border: 1px solid #8a5344;
  border-bottom-left-radius: 5px;
}

.clippy-msg.system {
  background-color: transparent;
  border: none;
  font-style: italic;
  padding: 2px 8px;
}

.clippy-msg.system label {
  color: #b39a8e;
  font-size: 11px;
}

.clippy-msg.error {
  background-color: #5a2e28;
  border: 1px solid #8a5344;
}

.clippy-msg.tool {
  background-color: transparent;
  border: none;
  padding: 1px 8px;
}

.clippy-msg.tool label {
  color: #9a8478;
  font-size: 11px;
}

.clippy-composer {
  padding-top: 8px;
}

.clippy-input,
window.clippy-bubble entry,
dialog.clippy-bubble entry {
  background-image: none;
  background-color: #1b1715;
  border: 1px solid #4a3f3a;
  border-radius: 16px;
  padding: 8px 12px;
  color: #eee3da;
  caret-color: #d37355;
  box-shadow: none;
  min-height: 30px;
}

window.clippy-bubble entry:focus,
.clippy-input:focus,
dialog.clippy-bubble entry:focus {
  border-color: #d37355;
  background-color: #211c19;
}

window.clippy-bubble entry selection,
.clippy-input selection,
.clippy-chrome label selection {
  background-color: #6b3d32;
  color: #eee3da;
}

window.clippy-bubble button,
.clippy-button,
dialog.clippy-bubble button {
  background-image: none;
  background-color: #3a332f;
  border: 1px solid #544840;
  border-radius: 12px;
  padding: 4px 10px;
  color: #eee3da;
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
  border-color: #b06651;
}

window.clippy-bubble button label,
.clippy-button label,
dialog.clippy-bubble button label {
  color: #eee3da;
  font-weight: 600;
}

window.clippy-bubble button:hover,
.clippy-button:hover,
dialog.clippy-bubble button:hover {
  background-image: none;
  background-color: #4a403b;
  border-color: #b06651;
}

window.clippy-bubble button:active,
.clippy-button:active,
dialog.clippy-bubble button:active {
  background-image: none;
  background-color: #5a3d34;
}

window.clippy-bubble button.clippy-text-btn {
  background-color: transparent;
  background-image: none;
  border: none;
  border-radius: 8px;
  min-height: 22px;
  padding: 2px 7px;
  color: #e08a6e;
}

window.clippy-bubble button.clippy-text-btn label {
  color: #e08a6e;
  font-weight: 600;
  font-size: 12px;
}

window.clippy-bubble button.clippy-text-btn:hover {
  background-color: #3a2a26;
  border: none;
}

window.clippy-bubble button.clippy-icon-btn {
  min-width: 28px;
  min-height: 28px;
  padding: 3px;
  border-radius: 14px;
  background-color: #3a332f;
  border: 1px solid #544840;
  color: #b39a8e;
}

window.clippy-bubble button.clippy-icon-btn:hover {
  background-color: #4a403b;
  border-color: #b06651;
  color: #eee3da;
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
  background-color: #3a2a26;
  border-color: #d37355;
  color: #e08a6e;
}

window.clippy-bubble button.destructive label,
.clippy-button.destructive label {
  color: #e08a6e;
}

window.clippy-bubble button.destructive:hover,
.clippy-button.destructive:hover {
  background-color: #5a3d34;
}

window.clippy-bubble button:disabled,
.clippy-button:disabled {
  opacity: 0.42;
}

.clippy-key {
  background-color: #3a332f;
  border: 1px solid #8a5344;
  border-radius: 8px;
  padding: 3px 8px;
}

.clippy-key label {
  font-weight: 700;
  font-size: 12px;
  color: #e08a6e;
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
  background-color: #544840;
  border-radius: 8px;
  min-width: 7px;
}

scrollbar slider:hover {
  background-color: #b06651;
}

dialog.clippy-bubble {
  background-color: #25201c;
}

dialog.clippy-bubble button {
  background-image: none;
  background-color: #3a332f;
  border: 1px solid #544840;
  border-radius: 11px;
}
"""


def load_css() -> None:
    import clippy_xfce.gi_setup  # noqa: F401
    from gi.repository import Gdk, Gtk

    settings = Gtk.Settings.get_default()
    if settings is not None:
        settings.set_property("gtk-application-prefer-dark-theme", True)
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 200,
    )
