"""X11 screenshot and input backend for Claude Computer Use."""

from __future__ import annotations

import io
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from PIL import Image

from clippy_xfce.agent.scale import ScreenScaler, clamp

MODIFIERS = {
    "ctrl": "Control_L",
    "control": "Control_L",
    "alt": "Alt_L",
    "shift": "Shift_L",
    "super": "Super_L",
    "meta": "Super_L",
    "win": "Super_L",
    "cmd": "Super_L",
    "command": "Super_L",
}

NAMED_KEYS = {
    "return": "Return",
    "enter": "Return",
    "tab": "Tab",
    "esc": "Escape",
    "escape": "Escape",
    "space": "space",
    "backspace": "BackSpace",
    "delete": "Delete",
    "del": "Delete",
    "home": "Home",
    "end": "End",
    "pageup": "Page_Up",
    "pagedown": "Page_Down",
    "page_up": "Page_Up",
    "page_down": "Page_Down",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "insert": "Insert",
    "capslock": "Caps_Lock",
}


class ComputerBackend(Protocol):
    def size(self) -> tuple[int, int]: ...
    def pointer(self) -> tuple[int, int]: ...
    def screenshot(self) -> Image.Image: ...
    def move(self, x: int, y: int) -> None: ...
    def button(self, button: int, pressed: bool) -> None: ...
    def scroll(self, direction: str, amount: int) -> None: ...
    def key(self, key: str, pressed: bool) -> None: ...
    def type_text(self, text: str) -> None: ...


@dataclass
class FakeComputer:
    width: int = 1920
    height: int = 1200
    cursor: tuple[int, int] = (0, 0)
    events: list[tuple] | None = None
    image: Image.Image | None = None

    def __post_init__(self) -> None:
        self.events = [] if self.events is None else self.events
        if self.image is None:
            self.image = Image.new("RGB", (self.width, self.height), (40, 40, 50))

    def size(self) -> tuple[int, int]:
        return self.width, self.height

    def pointer(self) -> tuple[int, int]:
        return self.cursor

    def screenshot(self) -> Image.Image:
        assert self.image is not None
        return self.image.copy()

    def move(self, x: int, y: int) -> None:
        self.cursor = (x, y)
        self.events.append(("move", x, y))

    def button(self, button: int, pressed: bool) -> None:
        self.events.append(("button", button, pressed, self.cursor))

    def scroll(self, direction: str, amount: int) -> None:
        self.events.append(("scroll", direction, amount, self.cursor))

    def key(self, key: str, pressed: bool) -> None:
        self.events.append(("key", key, pressed))

    def type_text(self, text: str) -> None:
        self.events.append(("type", text))


class X11Computer:
    def __init__(self) -> None:
        from Xlib import X, display
        from Xlib.ext import xtest

        self._X = X
        self._xtest = xtest
        self.display = display.Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        if not self.display.query_extension("XTEST"):
            raise RuntimeError("XTEST extension is required for computer use")

    def size(self) -> tuple[int, int]:
        geom = self.root.get_geometry()
        return int(geom.width), int(geom.height)

    def pointer(self) -> tuple[int, int]:
        data = self.root.query_pointer()
        return int(data.root_x), int(data.root_y)

    def screenshot(self) -> Image.Image:
        width, height = self.size()
        try:
            raw = self.root.get_image(0, 0, width, height, self._X.ZPixmap, 0xFFFFFFFF)
            return Image.frombytes("RGB", (width, height), raw.data, "raw", "BGRX")
        except Exception:
            pass
        grabbed = _cli_screenshot(width, height)
        if grabbed is not None:
            return grabbed
        from clippy_xfce.gtkutil import run_on_ui

        via_gdk = run_on_ui(_gdk_screenshot, timeout=2.0)
        if via_gdk is not None:
            return via_gdk
        return Image.new("RGB", (width, height), (0, 0, 0))

    def move(self, x: int, y: int) -> None:
        self._xtest.fake_input(self.display, self._X.MotionNotify, x=int(x), y=int(y))
        self.display.sync()

    def button(self, button: int, pressed: bool) -> None:
        event = self._X.ButtonPress if pressed else self._X.ButtonRelease
        self._xtest.fake_input(self.display, event, button)
        self.display.sync()

    def scroll(self, direction: str, amount: int) -> None:
        mapping = {"up": 4, "down": 5, "left": 6, "right": 7}
        button = mapping.get(direction, 5)
        for _ in range(max(1, int(amount))):
            self.button(button, True)
            self.button(button, False)

    def _keycode(self, name: str) -> int:
        from Xlib import XK

        keysym = XK.string_to_keysym(name)
        if not keysym:
            keysym = XK.string_to_keysym(name.capitalize())
        if not keysym and len(name) == 1:
            keysym = XK.string_to_keysym(name)
        if not keysym:
            raise ValueError(f"Unknown key: {name}")
        code = self.display.keysym_to_keycode(keysym)
        if not code:
            raise ValueError(f"No keycode for {name}")
        return code

    def key(self, key: str, pressed: bool) -> None:
        event = self._X.KeyPress if pressed else self._X.KeyRelease
        self._xtest.fake_input(self.display, event, self._keycode(key))
        self.display.sync()

    def type_text(self, text: str) -> None:
        if _is_simple_ascii(text):
            for char in text:
                if char == "\n":
                    tap_key(self, "Return")
                    continue
                if char == "\t":
                    tap_key(self, "Tab")
                    continue
                shifted = char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'
                if shifted:
                    self.key("Shift_L", True)
                try:
                    self.key(_char_key(char), True)
                    self.key(_char_key(char), False)
                except ValueError:
                    if shifted:
                        self.key("Shift_L", False)
                    _paste(self, text)
                    return
                if shifted:
                    self.key("Shift_L", False)
            return
        _paste(self, text)


def _char_key(char: str) -> str:
    table = {
        " ": "space",
        "-": "minus",
        "=": "equal",
        "[": "bracketleft",
        "]": "bracketright",
        "\\": "backslash",
        ";": "semicolon",
        "'": "apostrophe",
        ",": "comma",
        ".": "period",
        "/": "slash",
        "`": "grave",
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0",
        "_": "minus",
        "+": "equal",
        "{": "bracketleft",
        "}": "bracketright",
        "|": "backslash",
        ":": "semicolon",
        '"': "apostrophe",
        "<": "comma",
        ">": "period",
        "?": "slash",
        "~": "grave",
    }
    if char in table:
        return table[char]
    return char.lower()


def _is_simple_ascii(text: str) -> bool:
    return all(ord(ch) < 127 and (ch.isprintable() or ch in "\n\t") for ch in text)


def _paste(backend: ComputerBackend, text: str) -> None:
    if shutil.which("xclip"):
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=False,
        )
        tap_combo(backend, ["Control_L", "v"])
        return
    for char in text:
        backend.type_text(char)


def _gdk_screenshot() -> Image.Image | None:
    try:
        import clippy_xfce.gi_setup  # noqa: F401
        from gi.repository import Gdk

        window = Gdk.get_default_root_window()
        if window is None:
            return None
        width, height = window.get_width(), window.get_height()
        pixbuf = Gdk.pixbuf_get_from_window(window, 0, 0, width, height)
        if pixbuf is None:
            return None
        success, raw = pixbuf.save_to_bufferv("png", [], [])
        if not success:
            return None
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _cli_screenshot(width: int, height: int) -> Image.Image | None:
    if shutil.which("import"):
        try:
            raw = subprocess.check_output(["import", "-window", "root", "png:-"], timeout=3)
            return Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception:
            return None
    return None


def parse_keys(spec: str) -> list[str]:
    if not spec:
        return []
    parts = [part.strip() for part in spec.replace("-", "+").split("+") if part.strip()]
    resolved: list[str] = []
    for part in parts:
        lower = part.lower()
        if lower in MODIFIERS:
            resolved.append(MODIFIERS[lower])
        elif lower in NAMED_KEYS:
            resolved.append(NAMED_KEYS[lower])
        elif len(part) == 1:
            resolved.append(_char_key(part))
        elif part.startswith("F") and part[1:].isdigit():
            resolved.append(f"F{int(part[1:])}")
        else:
            resolved.append(NAMED_KEYS.get(lower, part))
    return resolved


def tap_key(backend: ComputerBackend, key: str) -> None:
    backend.key(key, True)
    backend.key(key, False)


def tap_combo(backend: ComputerBackend, keys: list[str]) -> None:
    for key in keys:
        backend.key(key, True)
    for key in reversed(keys):
        backend.key(key, False)


def hold_keys(backend: ComputerBackend, keys: list[str], pressed: bool) -> None:
    iterable = keys if pressed else reversed(keys)
    for key in iterable:
        backend.key(key, pressed)


class ComputerUse:
    def __init__(
        self,
        backend: ComputerBackend | None = None,
        scaler: ScreenScaler | None = None,
        before_shot: Callable[[], None] | None = None,
        after_shot: Callable[[], None] | None = None,
        max_edge: int = 2576,
    ) -> None:
        self.backend = backend or X11Computer()
        width, height = self.backend.size()
        self.scaler = scaler or ScreenScaler(width, height, max_long_edge=max_edge)
        self.before_shot = before_shot
        self.after_shot = after_shot

    def refresh_scaler(self) -> None:
        width, height = self.backend.size()
        self.scaler = ScreenScaler(width, height, max_long_edge=self.scaler.max_long_edge)

    def screenshot_png(self, region: list[int] | None = None) -> bytes:
        from clippy_xfce.gtkutil import run_on_ui

        hidden = False
        if self.before_shot:
            try:
                run_on_ui(self.before_shot, timeout=2.0)
                hidden = True
                time.sleep(0.06)
            except Exception:
                hidden = False
        try:
            image = self.backend.screenshot().convert("RGB")
        finally:
            if hidden and self.after_shot:
                try:
                    run_on_ui(self.after_shot, timeout=2.0)
                except Exception:
                    pass
        if region:
            x0, y0, x1, y1 = self.scaler.region_to_screen(region)
            image = image.crop((x0, y0, x1, y1))
            target = self.scaler.shot_size
            image.thumbnail(target)
        else:
            image = image.resize(self.scaler.shot_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def _xy(self, coordinate: list[int] | tuple[int, int] | None) -> tuple[int, int]:
        if not coordinate:
            return self.backend.pointer()
        return self.scaler.to_screen(float(coordinate[0]), float(coordinate[1]))

    def move(self, coordinate: list[int] | None) -> str:
        x, y = self._xy(coordinate)
        self.backend.move(x, y)
        return f"moved to ({x}, {y})"

    def click(
        self,
        button: int,
        coordinate: list[int] | None = None,
        modifiers: str | None = None,
        times: int = 1,
    ) -> str:
        x, y = self._xy(coordinate)
        self.backend.move(x, y)
        keys = parse_keys(modifiers or "")
        hold_keys(self.backend, keys, True)
        try:
            for _ in range(max(1, times)):
                self.backend.button(button, True)
                self.backend.button(button, False)
                time.sleep(0.03)
        finally:
            hold_keys(self.backend, keys, False)
        return f"clicked button {button} x{times} at ({x}, {y})"

    def drag(self, start: list[int], end: list[int], modifiers: str | None = None) -> str:
        x0, y0 = self._xy(start)
        x1, y1 = self._xy(end)
        keys = parse_keys(modifiers or "")
        self.backend.move(x0, y0)
        hold_keys(self.backend, keys, True)
        self.backend.button(1, True)
        steps = max(8, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / 40))
        for i in range(1, steps + 1):
            self.backend.move(x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps)
            time.sleep(0.01)
        self.backend.button(1, False)
        hold_keys(self.backend, keys, False)
        return f"dragged ({x0}, {y0}) -> ({x1}, {y1})"

    def press(self, spec: str, repeat: int = 1) -> str:
        keys = parse_keys(spec)
        if not keys:
            raise ValueError("No key specified")
        for _ in range(clamp(int(repeat or 1), 1, 100)):
            tap_combo(self.backend, keys)
            time.sleep(0.02)
        return f"pressed {spec} x{repeat}"

    def hold(self, spec: str, duration: float) -> str:
        keys = parse_keys(spec)
        hold_keys(self.backend, keys, True)
        time.sleep(min(300.0, max(0.0, float(duration))))
        hold_keys(self.backend, keys, False)
        return f"held {spec} for {duration}s"

    def handle(self, name: str, payload: dict[str, Any]) -> tuple[str | bytes, bool]:
        """Return (text or png-bytes, is_image)."""
        action = payload.get("action") or name
        coordinate = payload.get("coordinate")
        modifiers = payload.get("text") if action not in {"type", "key", "hold_key"} else None
        if action == "screenshot":
            return self.screenshot_png(), True
        if action == "zoom":
            return self.screenshot_png(payload.get("region")), True
        if action == "mouse_move":
            return self.move(coordinate), False
        if action == "left_click":
            return self.click(1, coordinate, modifiers, 1), False
        if action == "right_click":
            return self.click(3, coordinate, modifiers, 1), False
        if action == "middle_click":
            return self.click(2, coordinate, modifiers, 1), False
        if action == "double_click":
            return self.click(1, coordinate, modifiers, 2), False
        if action == "triple_click":
            return self.click(1, coordinate, modifiers, 3), False
        if action == "left_click_drag":
            start = payload.get("start_coordinate") or coordinate
            end = payload.get("coordinate")
            return self.drag(start, end, modifiers), False
        if action == "left_mouse_down":
            self.backend.button(1, True)
            return "left mouse down", False
        if action == "left_mouse_up":
            self.backend.button(1, False)
            return "left mouse up", False
        if action == "scroll":
            if coordinate:
                self.move(coordinate)
            self.backend.scroll(str(payload.get("scroll_direction") or "down"), int(payload.get("scroll_amount") or 1))
            return "scrolled", False
        if action == "type":
            self.backend.type_text(str(payload.get("text") or ""))
            return "typed text", False
        if action == "key":
            return self.press(str(payload.get("text") or ""), int(payload.get("repeat") or 1)), False
        if action == "hold_key":
            return self.hold(str(payload.get("text") or ""), float(payload.get("duration") or 0.5)), False
        if action == "wait":
            time.sleep(min(300.0, max(0.0, float(payload.get("duration") or 0.5))))
            return "waited", False
        if action == "cursor_position":
            x, y = self.backend.pointer()
            sx, sy = self.scaler.to_shot(x, y)
            return f"X={sx}, Y={sy}", False
        raise ValueError(f"Unknown computer action: {action}")
