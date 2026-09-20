from clippy_xfce.ui.help import pretty_accel, shortcut_lines


def test_pretty_accel():
    assert pretty_accel("<Ctrl><Alt>c") == "Ctrl+Alt+C"
    assert pretty_accel("<Primary><Shift>space") == "Ctrl+Shift+space"


def test_shortcut_lines_include_dodge_only_when_on():
    idle = shortcut_lines("<Ctrl><Alt>c", "Shift", dodge=False)
    keys = [row[0] for row in idle]
    assert "Ctrl+Alt+C" in keys
    assert "Escape" in keys
    assert "Click the mascot" in keys
    assert not any(row[0].startswith("Hold ") for row in idle)
    held = shortcut_lines("<Ctrl><Alt>c", "Alt", dodge=True)
    assert ("Hold Alt", "Keep the mascot still so you can click it") in held
    assert ("Chat open", "The mascot stays put while the chat is open") in held
