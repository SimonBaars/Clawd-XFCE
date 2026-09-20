"""Selectable desktop mascots, including an animated Clawd."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from clippy_xfce.chroma import crop_transparent, key_background
from clippy_xfce.paths import cache_dir, frame_cache_dir, package_data, sound_cache_dir
from clippy_xfce.sprites import AgentDef, write_icon

ALGO = "clawd-anim-v3"
PAD = 22

MASCOTS: tuple[tuple[str, str], ...] = (
    ("Clippy", "Clippy"),
    ("Clawd", "Clawd — Claude"),
)
MASCOT_IDS = tuple(item[0] for item in MASCOTS)


def mascot_label(mascot_id: str) -> str:
    for key, label in MASCOTS:
        if key == mascot_id:
            return label
    return mascot_id


def clawd_source() -> Path:
    bundled = package_data() / "agents" / "Clawd" / "clawd.png"
    if bundled.exists():
        return bundled
    pictures = Path.home() / "Pictures" / "clawd.png"
    if pictures.exists():
        return pictures
    raise FileNotFoundError("Clawd artwork not found (expected data/agents/Clawd/clawd.png)")


def ensure_custom(name: str) -> tuple[AgentDef, Path, Path]:
    if name == "Clawd":
        return ensure_clawd()
    raise ValueError(f"Unknown mascot {name}")


def ensure_clawd() -> tuple[AgentDef, Path, Path]:
    source = clawd_source()
    dest = frame_cache_dir("Clawd")
    marker = dest / "manifest.json"
    stamp = {
        "algo": ALGO,
        "source": str(source),
        "mtime": int(source.stat().st_mtime),
        "size": source.stat().st_size,
    }
    cached = json.loads(marker.read_text()) if marker.exists() else {}
    if (
        cached.get("algo") == stamp["algo"]
        and cached.get("source") == stamp["source"]
        and cached.get("mtime") == stamp["mtime"]
        and cached.get("size") == stamp["size"]
        and (dest / "0_0.png").exists()
        and cached.get("frame")
    ):
        width, height = cached["frame"]
        write_icon(dest / "0_0.png")
        return _clawd_def(width, height), dest, sound_cache_dir("Clawd")

    poses = _pose_sheet(source)
    width, height = poses[0].size
    dest.mkdir(parents=True, exist_ok=True)
    for extra in dest.glob("*.png"):
        extra.unlink()
    for index, pose in enumerate(poses):
        pose.save(dest / f"{index}_0.png")
    write_icon(dest / "0_0.png")
    marker.write_text(
        json.dumps({**stamp, "frames": len(poses), "frame": [width, height]}),
        encoding="utf-8",
    )
    (cache_dir() / "clawd.png").write_bytes((dest / "0_0.png").read_bytes())
    return _clawd_def(width, height), dest, sound_cache_dir("Clawd")


def _pose_sheet(source: Path) -> list[Image.Image]:
    keyed = crop_transparent(key_background(Image.open(source)), padding=PAD)
    eyes = _eye_regions(keyed)
    body = _body_color(keyed)
    rest = keyed
    return [
        rest,
        _blink(rest, eyes, body),
        _shift_eyes(rest, eyes, body, -7, 0),
        _shift_eyes(rest, eyes, body, 7, 0),
        _shift_eyes(rest, eyes, body, 0, -5),
        _shift_eyes(rest, eyes, body, 0, 5),
        _shift_eyes(rest, eyes, body, -6, -4),
        _shift_eyes(rest, eyes, body, 6, -4),
        _shift_eyes(rest, eyes, body, -6, 4),
        _shift_eyes(rest, eyes, body, 6, 4),
        _nudge(rest, 0, -10),
        _nudge(rest, 0, -16),
        _squash(rest, 1.10, 0.86),
        _squash(rest, 0.92, 1.10),
        _tilt(rest, 11),
        _tilt(rest, -11),
        _shear_legs(rest, -10),
        _shear_legs(rest, 10),
        _shear_legs(rest, -16),
        _shear_legs(rest, 16),
        _tilt(_nudge(rest, 0, -10), -8),
        _blink(_squash(rest, 1.12, 0.84), eyes, body),
        _squash(_nudge(rest, 0, 4), 1.08, 0.90),
    ]


def _eye_regions(image: Image.Image) -> list[tuple[int, int, int, int]]:
    arr = np.asarray(image)
    black = (arr[..., 0] < 32) & (arr[..., 1] < 32) & (arr[..., 2] < 32) & (arr[..., 3] > 200)
    ys, xs = np.where(black)
    if xs.size == 0:
        return []
    mid = int(xs.mean())
    boxes = []
    for choose_left in (True, False):
        mask = xs <= mid if choose_left else xs > mid
        if not np.any(mask):
            continue
        boxes.append((int(xs[mask].min()), int(ys[mask].min()), int(xs[mask].max()), int(ys[mask].max())))
    return boxes


def _body_color(image: Image.Image) -> tuple[int, int, int, int]:
    arr = np.asarray(image)
    opaque = arr[..., 3] > 220
    if not np.any(opaque):
        return (211, 115, 85, 255)
    pixels = arr[opaque]
    # Skip near-black eyes when sampling the shell.
    shell = pixels[np.max(pixels[:, :3], axis=1) > 40]
    if shell.size == 0:
        shell = pixels
    color = np.median(shell, axis=0).astype(np.uint8)
    return int(color[0]), int(color[1]), int(color[2]), 255


def _eye_mask(region: np.ndarray, grow: bool = True) -> np.ndarray:
    rgb = region[..., :3]
    alpha = region[..., 3]
    dark = (np.max(rgb, axis=-1) < 90) & (alpha > 180)
    if not grow:
        return dark
    padded = np.pad(dark, 2, mode="constant")
    grown = np.zeros_like(dark)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            grown |= padded[2 + dy : 2 + dy + dark.shape[0], 2 + dx : 2 + dx + dark.shape[1]]
    return grown & (alpha > 180)


def _fill_eyes(arr: np.ndarray, eyes: list[tuple[int, int, int, int]], body: tuple[int, int, int, int]) -> np.ndarray:
    out = arr.copy()
    color = np.array(body, dtype=np.uint8)
    for x0, y0, x1, y1 in eyes:
        x0, y0 = max(0, x0 - 2), max(0, y0 - 2)
        x1, y1 = min(arr.shape[1] - 1, x1 + 2), min(arr.shape[0] - 1, y1 + 2)
        region = out[y0 : y1 + 1, x0 : x1 + 1]
        region[_eye_mask(region)] = color
    return out


def _blink(image: Image.Image, eyes: list[tuple[int, int, int, int]], body: tuple[int, int, int, int]) -> Image.Image:
    arr = _fill_eyes(np.array(image), eyes, body)
    out = Image.fromarray(arr, "RGBA")
    for x0, y0, x1, y1 in eyes:
        mid = (y0 + y1) // 2
        out.paste((18, 14, 12, 255), (x0, mid, x1 + 1, min(mid + 3, y1 + 1)))
    return out


def _shift_eyes(
    image: Image.Image,
    eyes: list[tuple[int, int, int, int]],
    body: tuple[int, int, int, int],
    dx: int,
    dy: int,
) -> Image.Image:
    src = np.array(image)
    out = _fill_eyes(src, eyes, body)
    height, width = src.shape[:2]
    for x0, y0, x1, y1 in eyes:
        region = src[y0 : y1 + 1, x0 : x1 + 1]
        mask = _eye_mask(region, grow=False)
        dest_y0, dest_x0 = y0 + dy, x0 + dx
        for iy, ix in zip(*np.where(mask), strict=False):
            y, x = dest_y0 + int(iy), dest_x0 + int(ix)
            if 0 <= y < height and 0 <= x < width:
                out[y, x] = src[y0 + int(iy), x0 + int(ix)]
    return Image.fromarray(out, "RGBA")


def _nudge(image: Image.Image, dx: int, dy: int) -> Image.Image:
    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas.paste(image, (dx, dy), image)
    return canvas


def _squash(image: Image.Image, scale_x: float, scale_y: float) -> Image.Image:
    width, height = image.size
    new = (max(8, int(width * scale_x)), max(8, int(height * scale_y)))
    scaled = image.resize(new, Image.Resampling.BILINEAR)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = (width - scaled.width) // 2
    y = height - scaled.height - 4
    canvas.paste(scaled, (x, max(0, y)), scaled)
    return canvas


def _tilt(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(degrees, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(0, 0, 0, 0))


def _shear_legs(image: Image.Image, amount: int) -> Image.Image:
    arr = np.array(image)
    height, width = arr.shape[:2]
    start = int(height * 0.58)
    out = arr.copy()
    for y in range(start, height):
        t = (y - start) / max(height - start, 1)
        shift = int(round(amount * t))
        row = np.roll(arr[y], shift, axis=0)
        if shift > 0:
            row[:shift] = 0
        elif shift < 0:
            row[shift:] = 0
        out[y] = row
    return Image.fromarray(out, "RGBA")


def _frames(*pairs: tuple[int, int]) -> dict[str, Any]:
    return {"frames": [{"duration": duration, "images": [[index, 0]]} for index, duration in pairs]}


def _clawd_def(width: int, height: int) -> AgentDef:
    rest = _frames((0, 220))
    blink = _frames((0, 400), (1, 90), (0, 180))
    look_left = _frames((0, 120), (2, 420), (0, 160))
    look_right = _frames((0, 120), (3, 420), (0, 160))
    look_up = _frames((0, 100), (4, 380), (0, 140))
    look_down = _frames((0, 100), (5, 380), (0, 140))
    wave = _frames((0, 80), (16, 90), (18, 90), (16, 90), (17, 90), (19, 90), (17, 90), (0, 140))
    greet = _frames((0, 80), (10, 90), (11, 90), (20, 100), (16, 90), (18, 90), (17, 90), (1, 90), (0, 160))
    think = _frames((0, 80), (14, 140), (6, 180), (4, 180), (7, 180), (14, 140), (1, 90), (0, 120))
    search = _frames((0, 70), (2, 120), (3, 120), (2, 120), (3, 120), (4, 140), (0, 100))
    process = _frames((0, 70), (12, 100), (13, 100), (12, 100), (13, 100), (1, 80), (0, 100))
    talk = _frames((0, 80), (13, 90), (0, 90), (10, 90), (0, 90), (15, 90), (0, 100))
    gesture_r = _frames((0, 80), (15, 100), (17, 110), (15, 100), (0, 120))
    gesture_u = _frames((0, 80), (11, 110), (4, 140), (10, 100), (0, 120))
    act = _frames((0, 70), (16, 80), (19, 80), (17, 80), (18, 80), (12, 90), (0, 100))
    win = _frames((0, 70), (11, 90), (10, 90), (11, 90), (1, 80), (17, 90), (0, 140))
    alert = _frames((0, 60), (21, 120), (12, 100), (21, 120), (0, 140))
    attention = _frames((0, 70), (13, 90), (11, 90), (1, 80), (13, 90), (0, 120))
    side = _frames((0, 90), (14, 140), (0, 90), (15, 140), (0, 120))
    snooze = _frames((0, 200), (1, 160), (0, 240), (1, 160), (0, 200))
    hide = _frames((0, 70), (12, 90), (22, 110), (0, 80))
    show = _frames((22, 80), (12, 80), (10, 90), (0, 140))
    goodbye = _frames((0, 80), (17, 100), (16, 100), (17, 100), (12, 90), (0, 120))
    write = _frames((0, 80), (8, 120), (5, 120), (9, 120), (0, 100))
    artsy = _frames((0, 80), (14, 100), (20, 110), (15, 100), (11, 90), (0, 120))
    return AgentDef(
        name="Clawd",
        overlay_count=1,
        frame_size=(width, height),
        animations={
            "RestPose": rest,
            "Greeting": greet,
            "Wave": wave,
            "Show": show,
            "Hide": hide,
            "GoodBye": goodbye,
            "Thinking": think,
            "Processing": process,
            "Searching": search,
            "CheckingSomething": search,
            "Hearing_1": look_left,
            "Writing": write,
            "Print": process,
            "Save": write,
            "Explain": talk,
            "GestureRight": gesture_r,
            "GestureUp": gesture_u,
            "GetTechy": act,
            "Congratulate": win,
            "GetArtsy": artsy,
            "Alert": alert,
            "GetAttention": attention,
            "Idle1_1": blink,
            "IdleAtom": process,
            "IdleEyeBrowRaise": look_up,
            "IdleFingerTap": act,
            "IdleHeadScratch": think,
            "IdleRopePile": snooze,
            "IdleSideToSide": side,
            "IdleSnooze": snooze,
            "LookLeft": look_left,
            "LookRight": look_right,
            "LookUp": look_up,
            "LookDown": look_down,
            "LookUpLeft": _frames((0, 100), (6, 400), (0, 140)),
            "LookUpRight": _frames((0, 100), (7, 400), (0, 140)),
            "LookDownLeft": _frames((0, 100), (8, 400), (0, 140)),
            "LookDownRight": _frames((0, 100), (9, 400), (0, 140)),
        },
        sounds=[],
    )
