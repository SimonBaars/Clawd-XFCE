from clippy_xfce.ui.hotkey import EscapeWatch, HeldHotkey


def test_held_hotkey_binds_once(monkeypatch):
    calls: list[tuple] = []

    monkeypatch.setattr(
        "clippy_xfce.ui.hotkey.bind_hotkey",
        lambda accel, cb: calls.append(("bind", accel, cb)) or True,
    )
    monkeypatch.setattr(
        "clippy_xfce.ui.hotkey.unbind_hotkey",
        lambda accel: calls.append(("unbind", accel)),
    )

    def stop() -> None:
        return None

    held = HeldHotkey("Escape", stop)
    assert held.acquire() is True
    assert held.acquire() is True
    held.release()
    held.release()
    assert [item[0] for item in calls] == ["bind", "unbind"]
    assert calls[0][1] == "Escape"
    assert calls[1][1] == "Escape"


def test_held_hotkey_retries_after_failed_bind(monkeypatch):
    results = iter([False, True])
    binds: list[str] = []

    monkeypatch.setattr(
        "clippy_xfce.ui.hotkey.bind_hotkey",
        lambda accel, cb: binds.append(accel) or next(results),
    )
    monkeypatch.setattr("clippy_xfce.ui.hotkey.unbind_hotkey", lambda accel: None)

    held = HeldHotkey("Escape", lambda: None)
    assert held.acquire() is False
    assert held.bound is False
    assert held.acquire() is True
    assert binds == ["Escape", "Escape"]


def test_escape_watch_fires_on_press_edge():
    hits: list[int] = []
    watch = EscapeWatch(lambda: hits.append(1))
    watch._keycode = 9
    watch._display = object()
    states = iter([False, True, True, False])
    watch.query_down = lambda: next(states)
    watch._poll()
    watch._poll()
    watch._poll()
    watch._poll()
    assert hits == [1]


def test_escape_watch_ignores_keys_while_disarmed():
    hits: list[int] = []
    watch = EscapeWatch(lambda: hits.append(1), armed=lambda: False)
    watch._keycode = 9
    watch._display = object()
    watch.query_down = lambda: True
    watch._poll()
    assert hits == []


def test_held_hotkey_defers_unbind_inside_callback(monkeypatch):
    unbound: list[str] = []
    scheduled: list = []
    monkeypatch.setattr("clippy_xfce.ui.hotkey.bind_hotkey", lambda accel, cb: True)
    monkeypatch.setattr(
        "clippy_xfce.ui.hotkey.unbind_hotkey",
        lambda accel: unbound.append(accel),
    )

    import gi

    gi.require_version("GLib", "2.0")
    from gi.repository import GLib

    monkeypatch.setattr(GLib, "idle_add", lambda fn: scheduled.append(fn) or 1)

    held = HeldHotkey("Escape", lambda: None)
    assert held.acquire() is True
    held._inside = True
    held.release()
    assert unbound == []
    assert held.bound is False
    scheduled[0]()
    assert unbound == ["Escape"]
