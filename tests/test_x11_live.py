import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="needs an X display")


def test_real_screenshot_and_cursor():
    from clippy_xfce.agent.computer import ComputerUse, X11Computer

    computer = ComputerUse(X11Computer())
    png, is_image = computer.handle("screenshot", {})
    assert is_image and png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 5000
    text, _ = computer.handle("cursor_position", {})
    assert text.startswith("X=")
    x0, y0 = computer.backend.pointer()
    computer.handle("mouse_move", {"coordinate": [x0, y0]})
    assert computer.backend.pointer() == (x0, y0)
