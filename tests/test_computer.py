import threading
import time

from PIL import Image

from clippy_xfce.agent.computer import ComputerUse, FakeComputer, parse_keys
from clippy_xfce.agent.scale import ScreenScaler


def test_parse_keys():
    assert parse_keys("ctrl+s") == ["Control_L", "s"]
    assert parse_keys("Return") == ["Return"]
    assert parse_keys("alt+Tab") == ["Alt_L", "Tab"]
    assert parse_keys("shift+F5") == ["Shift_L", "F5"]
    assert parse_keys("super+Left") == ["Super_L", "Left"]


def test_screenshot_can_skip_hide():
    seen: list[str] = []
    computer = ComputerUse(
        FakeComputer(),
        ScreenScaler(1920, 1200),
        before_shot=lambda: seen.append("hide"),
        after_shot=lambda: seen.append("show"),
    )
    computer.screenshot_png(hide=False)
    assert seen == []
    computer.screenshot_png(hide=True)
    assert seen == ["hide", "show"]


def test_fake_actions():
    backend = FakeComputer()
    computer = ComputerUse(backend, ScreenScaler(1920, 1200))
    png, is_image = computer.handle("screenshot", {})
    assert is_image and png[:8] == b"\x89PNG\r\n\x1a\n"
    computer.handle("mouse_move", {"coordinate": [100, 80]})
    assert backend.cursor == (100, 80)
    computer.handle("left_click", {"coordinate": [10, 20], "text": "shift"})
    kinds = [event[0] for event in backend.events]
    assert kinds.count("button") >= 2
    computer.handle("type", {"text": "hello"})
    assert ("type", "hello") in backend.events
    computer.handle("key", {"text": "ctrl+s", "repeat": 1})
    computer.handle("scroll", {"scroll_direction": "down", "scroll_amount": 2, "coordinate": [50, 50]})
    text, _ = computer.handle("cursor_position", {})
    assert text.startswith("X=")
    computer.handle("wait", {"duration": 0.01})
    zoom, is_zoom = computer.handle("zoom", {"region": [0, 0, 200, 100]})
    assert is_zoom and zoom[:8] == b"\x89PNG\r\n\x1a\n"
    computer.handle("left_click_drag", {"start_coordinate": [0, 0], "coordinate": [40, 10]})
    computer.handle("double_click", {"coordinate": [8, 8]})
    computer.handle("right_click", {"coordinate": [8, 8]})
    computer.handle("left_mouse_down", {})
    computer.handle("left_mouse_up", {})


def test_legacy_action_field():
    backend = FakeComputer(image=Image.new("RGB", (1920, 1200), (9, 9, 9)))
    computer = ComputerUse(backend)
    computer.handle("computer", {"action": "mouse_move", "coordinate": [3, 4]})
    assert backend.cursor == (3, 4)


def test_wait_is_short():
    backend = FakeComputer()
    computer = ComputerUse(backend)
    start = time.time()
    computer.handle("wait", {"duration": 0.02})
    assert time.time() - start < 1


def test_wait_stops_when_cancelled():
    state = {"stop": False}
    computer = ComputerUse(FakeComputer(), cancelled=lambda: state["stop"])
    start = time.monotonic()

    def flip() -> None:
        time.sleep(0.06)
        state["stop"] = True

    threading.Thread(target=flip, daemon=True).start()
    text, _ = computer.handle("wait", {"duration": 2})
    assert text == "cancelled"
    assert time.monotonic() - start < 0.6


def test_cancelled_action_does_not_engage():
    seen: list[str] = []
    computer = ComputerUse(
        FakeComputer(),
        on_engage=lambda: seen.append("hide"),
        cancelled=lambda: True,
    )
    text, _ = computer.handle("wait", {"duration": 0.01})
    assert text == "cancelled"
    assert seen == []
