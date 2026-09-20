"""Flee when the pointer gets close; stay put while a hold key is down."""

from __future__ import annotations

import math
from typing import Iterable

HOLD_KEYS = ("Shift", "Ctrl", "Alt", "Super")
MARGIN = 56
HOP = 170

# Gdk.ModifierType bits
SHIFT_MASK = 1 << 0
CONTROL_MASK = 1 << 2
MOD1_MASK = 1 << 3
MOD4_MASK = 1 << 6
SUPER_MASK = 1 << 26

_HOLD_ALIASES = {
    "shift": "Shift",
    "<shift>": "Shift",
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "<ctrl>": "Ctrl",
    "<control>": "Ctrl",
    "alt": "Alt",
    "<alt>": "Alt",
    "super": "Super",
    "meta": "Super",
    "<super>": "Super",
}


def normalize_hold_key(name: str) -> str:
    raw = (name or "Shift").strip()
    return _HOLD_ALIASES.get(raw.lower(), raw if raw in HOLD_KEYS else "Shift")


def hold_is_down(hold_key: str, modifiers: int) -> bool:
    key = normalize_hold_key(hold_key)
    if key == "Shift":
        return bool(modifiers & SHIFT_MASK)
    if key == "Ctrl":
        return bool(modifiers & CONTROL_MASK)
    if key == "Alt":
        return bool(modifiers & MOD1_MASK)
    if key == "Super":
        return bool(modifiers & (SUPER_MASK | MOD4_MASK))
    return False


def pointer_hits(mx: float, my: float, x: int, y: int, w: int, h: int, margin: int = MARGIN) -> bool:
    return x - margin <= mx <= x + w + margin and y - margin <= my <= y + h + margin


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _clamp_pos(x: int, y: int, w: int, h: int, work: tuple[int, int, int, int]) -> tuple[int, int]:
    wx, wy, ww, wh = work
    return (
        _clamp(x, wx + 8, max(wx + 8, wx + ww - w - 8)),
        _clamp(y, wy + 8, max(wy + 8, wy + wh - h - 8)),
    )


def flee_position(
    mx: float,
    my: float,
    x: int,
    y: int,
    w: int,
    h: int,
    work: tuple[int, int, int, int],
    margin: int = MARGIN,
    hop: int = HOP,
) -> tuple[int, int]:
    """Pick a work-area point where the padded mascot no longer contains the pointer."""
    cx = x + w / 2
    cy = y + h / 2
    dx = cx - mx
    dy = cy - my
    if abs(dx) + abs(dy) < 1:
        dx, dy = -1.0, -0.35
    heading = math.atan2(dy, dx)
    need = max(w, h) / 2 + margin + 28
    distances = (max(hop, int(need)), hop + 90, hop + 180)
    offsets = (0, math.pi / 4, -math.pi / 4, math.pi / 2, -math.pi / 2, 3 * math.pi / 4, -3 * math.pi / 4, math.pi)
    for dist in distances:
        for offset in offsets:
            ang = heading + offset
            nx = int(round(mx + math.cos(ang) * dist - w / 2))
            ny = int(round(my + math.sin(ang) * dist - h / 2))
            nx, ny = _clamp_pos(nx, ny, w, h, work)
            if (nx, ny) == (x, y):
                continue
            if not pointer_hits(mx, my, nx, ny, w, h, margin):
                return nx, ny
    wx, wy, ww, wh = work
    opposite = _clamp_pos(wx + ww - (x - wx) - w, wy + wh - (y - wy) - h, w, h, work)
    return opposite


def skitter_steps(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    count: int = 8,
    work: tuple[int, int, int, int] | None = None,
    size: tuple[int, int] = (1, 1),
) -> list[tuple[int, int]]:
    """Ease-out hop with a small sideways wobble."""
    steps: list[tuple[int, int]] = []
    across = x1 - x0
    down = y1 - y0
    for index in range(1, count + 1):
        t = index / count
        ease = 1 - (1 - t) ** 2
        wobble = math.sin(t * math.pi * 2) * 10
        px = int(round(x0 + across * ease + (-down / max(abs(down) + abs(across), 1)) * wobble))
        py = int(round(y0 + down * ease + (across / max(abs(down) + abs(across), 1)) * wobble))
        if work:
            px, py = _clamp_pos(px, py, size[0], size[1], work)
        steps.append((px, py))
    if steps:
        last = (x1, y1)
        if work:
            last = _clamp_pos(x1, y1, size[0], size[1], work)
        steps[-1] = last
    return steps


def iter_hold_keys() -> Iterable[str]:
    return HOLD_KEYS
