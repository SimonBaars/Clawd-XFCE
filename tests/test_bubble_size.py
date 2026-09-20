import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="needs an X display")


def _pump():
    from gi.repository import Gtk

    for _ in range(24):
        Gtk.main_iteration_do(False)


def test_send_does_not_grow_the_bubble():
    import clippy_xfce.gi_setup  # noqa: F401
    from gi.repository import Gtk

    from clippy_xfce.ui.bubble import BUBBLE_HEIGHT, BUBBLE_WIDTH, BubbleWindow
    from clippy_xfce.ui.theme import load_css

    load_css()
    Gtk.init([])
    win = BubbleWindow()
    win.add_message("assistant", "Hi! I'm Clawd.")
    win.show_all()
    _pump()
    assert win.get_size() == (BUBBLE_WIDTH, BUBBLE_HEIGHT)
    win.add_message("user", "explain how to init a git repo")
    win.set_busy(True, "Working on the desktop…  tray Stop or Ctrl+Alt+C to steer.")
    _pump()
    assert win.get_size() == (BUBBLE_WIDTH, BUBBLE_HEIGHT)
    win.destroy()
