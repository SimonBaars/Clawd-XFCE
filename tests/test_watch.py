from clippy_xfce.watch import (
    SAMPLE_H,
    SAMPLE_W,
    Frame,
    WatchSession,
    WatchSpec,
    infer_match,
    looks_like_stop_supervise,
    looks_like_supervise,
    on_idle_prompt,
    run_watch,
    spec_from_payload,
)


def _digest(value: int) -> bytes:
    return bytes([value] * (SAMPLE_W * SAMPLE_H))


def test_detects_supervise_wording():
    assert looks_like_supervise(
        "monitor the agent running in the active coding window, and schedule a next dev task every time it finishes"
    )
    assert looks_like_supervise("watch Cursor and queue the next task when it is done")
    assert not looks_like_supervise("open firefox and search for puppies")
    assert looks_like_stop_supervise("stop watching the cursor window")
    assert not looks_like_supervise("stop watching the cursor window")


def test_infer_match_from_text():
    assert infer_match("watch the Cursor window") == "cursor"
    assert infer_match("monitor the active coding window") == "active"


def test_session_waits_for_busy_then_idle():
    session = WatchSession(WatchSpec(idle_seconds=1.0, require_busy=True))
    still = Frame("repo", "Cursor", _digest(10))
    assert session.feed(still, now=100.0) is None
    assert session.phase == "seek_busy"
    busy = Frame("repo", "Cursor", _digest(80))
    assert session.feed(busy, now=100.4) is None
    assert session.phase == "seek_idle"
    assert session.feed(Frame("repo", "Cursor", _digest(80)), now=100.8) is None
    done = session.feed(Frame("repo", "Cursor", _digest(80)), now=102.0)
    assert done is not None
    assert done.status == "idle"
    assert done.title == "repo"


def test_busy_title_counts_as_activity():
    session = WatchSession(WatchSpec(idle_seconds=0.5, require_busy=True))
    assert session.feed(Frame("Generating…", "Cursor", _digest(10)), now=1.0) is None
    assert session.phase == "seek_idle"
    assert session.feed(Frame("repo", "Cursor", _digest(10)), now=1.2) is None
    assert session.feed(Frame("repo", "Cursor", _digest(10)), now=1.8) is None
    done = session.feed(Frame("repo", "Cursor", _digest(10)), now=2.4)
    assert done is not None and done.status == "idle"


def test_run_watch_can_be_cancelled():
    frames = iter(
        [
            Frame("a", "Cursor", _digest(1)),
            Frame("a", "Cursor", _digest(90)),
            Frame("a", "Cursor", _digest(90)),
        ]
    )
    stop = {"n": 0}

    def snap(_match: str) -> Frame:
        stop["n"] += 1
        return next(frames)

    result = run_watch(
        WatchSpec(idle_seconds=30, poll_seconds=0.01),
        snap,
        cancelled=lambda: stop["n"] >= 2,
        sleep=lambda _s: None,
    )
    assert result.status == "cancelled"


def test_spec_and_idle_prompt():
    spec = spec_from_payload({"window": "cursor", "idle_seconds": 12}, "watch me")
    assert spec.match == "cursor"
    assert spec.idle_seconds == 12
    text = on_idle_prompt("queue the next task")
    assert "queue the next task" in text
    assert "do not poll" in text.lower()


def test_timeout_and_gone():
    session = WatchSession(WatchSpec(idle_seconds=8, timeout_seconds=2, require_busy=True), started=5.0)
    session.feed(Frame("a", "X", _digest(1)), now=5.0)
    timed = session.feed(Frame("a", "X", _digest(1)), now=8.0)
    assert timed is not None and timed.status == "timeout"
    session = WatchSession(WatchSpec(require_busy=False, idle_seconds=8))
    session.feed(Frame("a", "X", _digest(1)), now=1.0)
    gone = session.feed(None, now=1.2)
    assert gone is not None and gone.status == "gone"
