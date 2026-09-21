"""Cheap local watcher: title + tiny frame hash, no Claude until idle."""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from clippy_xfce.agent.context import is_assistant_window

BUSY_TITLE = re.compile(
    r"generat|thinking|wait(?:ing)?|working|\.\.\.|…|claude is|\bagent\b|running",
    re.I,
)

MONITOR_RE = re.compile(
    r"""(?ix)
    \b(
        monitor |
        watch(?:ing)? |
        keep\ an\ eye |
        whenever\ it\ finishes |
        every\ time\ (?:it|the\ agent)\ finishes |
        when\ (?:it|the\ agent|that)\ (?:is\ )?(?:done|finished|finishes) |
        schedule\ (?:a\ )?next |
        queue\ (?:the\ )?next |
        babysit
    )\b
    """
)

APP_HINTS = (
    "cursor",
    "code",
    "vscode",
    "vscodium",
    "firefox",
    "terminal",
    "xfce4-terminal",
    "thunar",
    "mousepad",
    "chrome",
    "chromium",
)

DEFAULT_IDLE = 8.0
DEFAULT_POLL = 0.55
SAMPLE_W = 48
SAMPLE_H = 28
CHANGE_THRESHOLD = 0.018


@dataclass
class WatchSpec:
    match: str = "active"
    idle_seconds: float = DEFAULT_IDLE
    timeout_seconds: float = 0.0
    require_busy: bool = True
    poll_seconds: float = DEFAULT_POLL


@dataclass
class Frame:
    title: str
    app: str
    digest: bytes | None
    xid: int = 0


@dataclass
class WatchResult:
    status: str
    title: str = ""
    app: str = ""
    waited: float = 0.0
    detail: str = ""

    def text(self) -> str:
        who = self.title or self.app or "window"
        extra = f" ({self.app})" if self.app and self.app not in who else ""
        if self.status == "idle":
            return f"Idle after {self.waited:.0f}s: {who}{extra}. {self.detail}".strip()
        if self.status == "cancelled":
            return "Watch cancelled."
        if self.status == "timeout":
            return f"Watch timed out after {self.waited:.0f}s still on {who}{extra}."
        if self.status == "gone":
            return f"Watched window disappeared after {self.waited:.0f}s."
        return f"{self.status}: {who}"


@dataclass
class WatchSession:
    spec: WatchSpec
    phase: str = ""
    idle_from: float | None = None
    last: Frame | None = None
    started: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        if not self.phase:
            self.phase = "seek_busy" if self.spec.require_busy else "seek_idle"

    def feed(self, frame: Frame | None, now: float | None = None) -> WatchResult | None:
        now = time.monotonic() if now is None else now
        waited = now - self.started
        if self.spec.timeout_seconds and waited >= self.spec.timeout_seconds:
            last = self.last
            return WatchResult(
                "timeout",
                title=last.title if last else "",
                app=last.app if last else "",
                waited=waited,
            )
        if frame is None:
            if self.last is not None:
                return WatchResult("gone", self.last.title, self.last.app, waited)
            return None
        changing = self._changed(frame)
        title_busy = bool(BUSY_TITLE.search(frame.title or ""))
        self.last = frame
        if changing or title_busy:
            self.idle_from = None
            if self.phase == "seek_busy":
                self.phase = "seek_idle"
            return None
        if self.phase == "seek_busy":
            return None
        if self.idle_from is None:
            self.idle_from = now
        if now - self.idle_from >= self.spec.idle_seconds:
            return WatchResult(
                "idle",
                title=frame.title,
                app=frame.app,
                waited=waited,
                detail="pixels and title stayed still",
            )
        return None

    def _changed(self, frame: Frame) -> bool:
        prev = self.last
        if prev is None:
            return False
        if (frame.title or "") != (prev.title or ""):
            return True
        if frame.digest is None or prev.digest is None:
            return False
        if len(frame.digest) != len(prev.digest) or not frame.digest:
            return True
        total = sum(abs(a - b) for a, b in zip(frame.digest, prev.digest, strict=False))
        return (total / (len(frame.digest) * 255)) > CHANGE_THRESHOLD


STOP_RE = re.compile(
    r"\b(stop|don't|dont|cancel|quit)\b.{0,24}\b(watching|monitoring|supervising|supervise)\b",
    re.I,
)


def looks_like_stop_supervise(text: str) -> bool:
    return bool(STOP_RE.search(text or ""))


def looks_like_supervise(text: str) -> bool:
    blob = text or ""
    if looks_like_stop_supervise(blob):
        return False
    return bool(MONITOR_RE.search(blob))


def infer_match(text: str) -> str:
    blob = (text or "").lower()
    for hint in APP_HINTS:
        if hint in blob:
            return "code" if hint == "vscode" else hint
    return "active"


def spec_from_payload(payload: dict | None = None, user_text: str = "") -> WatchSpec:
    data = payload or {}
    match = str(data.get("window") or data.get("match") or "").strip()
    if not match:
        match = infer_match(user_text)
    idle = _number(data.get("idle_seconds"), DEFAULT_IDLE)
    timeout = _number(data.get("timeout_seconds"), 0.0)
    require = data.get("require_busy")
    if require is None:
        require = True
    poll = _number(data.get("poll_seconds"), DEFAULT_POLL)
    return WatchSpec(
        match=match or "active",
        idle_seconds=min(120.0, max(2.0, idle)),
        timeout_seconds=max(0.0, timeout),
        require_busy=bool(require),
        poll_seconds=min(5.0, max(0.2, poll)),
    )


def on_idle_prompt(user_text: str, result: WatchResult | None = None) -> str:
    seen = result.text() if result else "The watched window just went idle after working."
    request = (user_text or "Queue the next development task.").strip()
    return (
        f"{seen}\n\nOriginal request:\n{request}\n\n"
        "Do the next step now in that window (type or queue the next task). "
        "Then finish this turn. Local idle detection continues — do not poll with screenshot and wait."
    )


def run_watch(
    spec: WatchSpec,
    snapshot: Callable[[str], Frame | None],
    cancelled: Callable[[], bool] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> WatchResult:
    session = WatchSession(spec)
    while True:
        if cancelled and cancelled():
            last = session.last
            return WatchResult(
                "cancelled",
                title=last.title if last else "",
                app=last.app if last else "",
                waited=clock() - session.started,
            )
        result = session.feed(snapshot(spec.match), clock())
        if result is not None:
            return result
        sleep(spec.poll_seconds)


def snapshot_window(match: str) -> Frame | None:
    """Live X11 snapshot. Safe to call from a worker thread."""
    try:
        return _x11_snapshot(match)
    except Exception:
        return None


def digest_image(image) -> bytes:
    small = image.convert("L").resize((SAMPLE_W, SAMPLE_H))
    return bytes(small.getdata())


def frame_fingerprint(digest: bytes) -> str:
    return hashlib.md5(digest).hexdigest()[:10]


def _number(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _x11_snapshot(match: str) -> Frame | None:
    from Xlib import display
    from Xlib.error import XError

    dpy = display.Display()
    try:
        root = dpy.screen().root
        clients = _client_xids(dpy, root)
        active = _active_xid(dpy, root)
        wanted = (match or "active").strip().lower()
        picked = None
        frames: list[tuple[int, str, str]] = []
        for xid in clients:
            try:
                win = dpy.create_resource_object("window", xid)
                title = _window_title(dpy, win)
                app = _window_app(win)
            except XError:
                continue
            if is_assistant_window(title, app):
                continue
            frames.append((xid, title, app))
            if wanted == "active" and xid == active:
                picked = (xid, title, app)
            elif wanted not in {"", "active"} and (wanted in title.lower() or wanted in app.lower()):
                if picked is None or xid == active:
                    picked = (xid, title, app)
        if picked is None and wanted == "active":
            picked = next((item for item in frames if item[0] != active), None)
            if picked is None and frames:
                picked = frames[0]
        if picked is None:
            return None
        xid, title, app = picked
        digest = _window_digest(dpy, xid)
        return Frame(title=title, app=app, digest=digest, xid=xid)
    finally:
        try:
            dpy.close()
        except Exception:
            pass


def _client_xids(dpy, root) -> list[int]:
    from Xlib import X

    atom = dpy.get_atom("_NET_CLIENT_LIST")
    prop = root.get_full_property(atom, X.AnyPropertyType)
    if not prop or not prop.value:
        return []
    return [int(item) for item in prop.value]


def _active_xid(dpy, root) -> int:
    from Xlib import X

    atom = dpy.get_atom("_NET_ACTIVE_WINDOW")
    prop = root.get_full_property(atom, X.AnyPropertyType)
    if not prop or not prop.value:
        return 0
    return int(prop.value[0])


def _window_title(dpy, win) -> str:
    utf8 = dpy.get_atom("UTF8_STRING")
    net = dpy.get_atom("_NET_WM_NAME")
    try:
        prop = win.get_full_property(net, utf8)
        if prop and prop.value:
            value = prop.value
            if isinstance(value, bytes):
                return value.decode("utf-8", "replace")
            return str(value)
    except Exception:
        pass
    try:
        return win.get_wm_name() or ""
    except Exception:
        return ""


def _window_app(win) -> str:
    try:
        klass = win.get_wm_class()
    except Exception:
        return ""
    if not klass:
        return ""
    return str(klass[1] or klass[0] or "")


def _window_digest(dpy, xid: int) -> bytes | None:
    from Xlib import X
    from PIL import Image

    try:
        win = dpy.create_resource_object("window", xid)
        geom = win.get_geometry()
        width = max(1, min(int(geom.width), 960))
        height = max(1, min(int(geom.height), 720))
        raw = win.get_image(0, 0, width, height, X.ZPixmap, 0xFFFFFFFF)
        image = Image.frombytes("RGB", (width, height), raw.data, "raw", "BGRX")
        return digest_image(image)
    except Exception:
        return None
