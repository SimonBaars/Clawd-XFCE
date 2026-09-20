from clippy_xfce.ui.hotkey import HeldHotkey


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
