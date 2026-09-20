from clippy_xfce.agent.context import is_assistant_window
from clippy_xfce.agent.prompts import PERSONALITY


def test_filters_own_mascot_windows():
    assert is_assistant_window("Clawd", "Clippy")
    assert is_assistant_window("Clippy", "")
    assert is_assistant_window("Ask Clippy", "org.xfce.clippy")
    assert not is_assistant_window("Firefox", "firefox")
    assert not is_assistant_window("Terminal", "xfce4-terminal")


def test_prompt_forbids_own_chat():
    assert "chat bubble are hidden" in PERSONALITY
    assert "Never click" in PERSONALITY
