import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="needs an X display")


def test_settings_and_history_dialogs():
    pytest.importorskip("gi")
    import clippy_xfce.gi_setup  # noqa: F401
    from gi.repository import Gtk

    from clippy_xfce.agent.memory import MemoryStore
    from clippy_xfce.config import Settings
    from clippy_xfce.ui.history import HistoryDialog
    from clippy_xfce.ui.settings import SettingsDialog
    from clippy_xfce.ui.theme import load_css

    load_css()
    settings = SettingsDialog(None, Settings(api_key="sk-ant-testkey-12345678901234567890"))
    result = settings.result_settings()
    assert result.model
    assert result.dodge_mouse is False
    assert result.dodge_hold_key == "Shift"
    settings.destroy()

    store = MemoryStore()
    dialog = HistoryDialog(None, store)
    dialog.refresh()
    dialog.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
