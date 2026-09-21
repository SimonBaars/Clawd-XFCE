from clippy_xfce.agent.memory import MemoryStore
from clippy_xfce.agent.tools import ToolHub, TextEditor, is_dangerous_bash, run_bash


def test_danger_detection():
    assert is_dangerous_bash("rm -rf /tmp/foo")
    assert is_dangerous_bash("sudo pacman -S x")
    assert not is_dangerous_bash("ls -la")
    assert not is_dangerous_bash("python -m pytest")


def test_bash_and_editor(tmp_path):
    path = tmp_path / "note.txt"
    editor = TextEditor()
    editor.handle({"command": "create", "path": str(path), "file_text": "hello world\n"})
    viewed = editor.handle({"command": "view", "path": str(path)})
    assert "hello world" in viewed
    editor.handle({"command": "str_replace", "path": str(path), "old_str": "hello", "new_str": "hi"})
    assert path.read_text() == "hi world\n"
    editor.handle({"command": "undo_edit", "path": str(path)})
    assert path.read_text() == "hello world\n"
    listing = editor.handle({"command": "view", "path": str(tmp_path)})
    assert "note.txt" in listing
    out = run_bash("echo clippy-ok", cwd=str(tmp_path))
    assert "clippy-ok" in out


def test_memory_tools(tmp_path):
    store = MemoryStore(tmp_path / "m.db")
    hub = ToolHub(store, express=lambda mood, anim: f"{mood}:{anim}")
    hub.handle("remember", {"text": "Likes XFCE panel on top", "kind": "preference"})
    recalled = hub.handle("recall", {"query": "panel"})
    assert "XFCE" in recalled
    assert "success:None" in hub.handle("express", {"mood": "success"})
    flashes: list[tuple[str, float]] = []
    talking = ToolHub(store, flash=lambda text, seconds: flashes.append((text, seconds)) or "flashed")
    assert talking.handle("flash", {"text": "Now we run git init.", "seconds": 4}) == "flashed"
    assert flashes == [("Now we run git init.", 4.0)]
    talking.handle("notify_user", {"body": "Opening the terminal."})
    assert flashes[-1][0] == "Opening the terminal."
    seen: list[str] = []
    watching = ToolHub(
        store,
        watch=lambda payload: seen.append(f"watch:{payload.get('window')}") or "idle",
        supervise=lambda payload: seen.append("arm") or "armed",
        stop_supervise=lambda: seen.append("stop") or "stopped",
    )
    assert watching.handle("watch_window", {"window": "cursor"}) == "idle"
    assert watching.handle("supervise", {"window": "active"}) == "armed"
    assert watching.handle("stop_supervise", {}) == "stopped"
    assert seen == ["watch:cursor", "arm", "stop"]
