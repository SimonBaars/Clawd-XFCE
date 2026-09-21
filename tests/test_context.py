from clippy_xfce.agent.context import is_assistant_window, is_terminal_window
from clippy_xfce.agent.prompts import PERSONALITY


def test_filters_own_mascot_windows():
    assert is_assistant_window("Clawd", "Clippy")
    assert is_assistant_window("Clippy", "")
    assert is_assistant_window("Ask Clippy", "org.xfce.clippy")
    assert not is_assistant_window("Firefox", "firefox")
    assert not is_assistant_window("Terminal", "xfce4-terminal")


def test_detects_terminal_windows():
    assert is_terminal_window("Terminal - simon@simon:~/tmp", "xfce4-terminal")
    assert is_terminal_window("", "kitty")
    assert not is_terminal_window("ch12.tex - The-Ordeals - Visual Studio Code", "code")


def test_prompt_forbids_own_chat():
    assert "chat bubble are hidden" in PERSONALITY
    assert "Never click" in PERSONALITY
    assert "flash" in PERSONALITY
    assert "Ctrl+Alt+Escape" in PERSONALITY
