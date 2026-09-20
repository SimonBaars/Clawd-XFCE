import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="needs an X display")


def test_character_and_bubble_realize():
    pytest.importorskip("gi")
    import clippy_xfce.gi_setup  # noqa: F401
    from gi.repository import Gtk

    from clippy_xfce.sounds import SoundPlayer
    from clippy_xfce.sprites import ensure_assets
    from clippy_xfce.ui.bubble import BubbleWindow
    from clippy_xfce.ui.character import CharacterWindow
    from clippy_xfce.ui.theme import load_css

    agent, frames, _sounds = ensure_assets()
    load_css()
    sounds = SoundPlayer(enabled=False)
    character = CharacterWindow(agent, frames, 1.5, sounds)
    bubble = BubbleWindow()
    character.place_default()
    character.show_all()
    bubble.add_message("assistant", "It looks like you're testing me.")
    bubble.show_all()
    bubble.place_near(character)
    for _ in range(12):
        Gtk.main_iteration_do(False)
    assert character.get_allocated_width() > 0
    assert bubble.get_allocated_width() > 0
    character.play("Wave", interrupt=True)
    Gtk.main_iteration_do(False)
    character.destroy()
    bubble.destroy()
