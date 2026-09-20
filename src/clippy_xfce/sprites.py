"""Parse clippy.js agent data and cache sprite frames."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from PIL import Image

from clippy_xfce.paths import agent_source_dir, cache_dir, frame_cache_dir, sound_cache_dir
from clippy_xfce.upscale import UPSCALE, enhance_dir

AGENT_JS_RE = re.compile(r"clippy\.ready\(\s*'[^']+'\s*,\s*", re.S)
SOUNDS_JS_RE = re.compile(r"clippy\.soundsReady\(\s*'[^']+'\s*,\s*", re.S)
DATA_URI_RE = re.compile(r"^data:([^;]+);base64,(.+)$", re.S)
SOUND_PAIR_RE = re.compile(r"""['"](\d+)['"]\s*:\s*['"](data:audio[^'"]+)['"]""")


@dataclass(frozen=True)
class AgentDef:
    name: str
    overlay_count: int
    frame_size: tuple[int, int]
    animations: dict[str, dict[str, Any]]
    sounds: list[str]


def parse_js_object(text: str, header_re: re.Pattern[str]) -> dict[str, Any]:
    match = header_re.search(text)
    if not match:
        start = text.find("{")
        blob = text[start:]
    else:
        blob = text[match.end() :]
    blob = blob.strip()
    if blob.endswith(");"):
        blob = blob[:-2]
    elif blob.endswith(")"):
        blob = blob[:-1]
    blob = blob.strip()
    if blob.endswith(";"):
        blob = blob[:-1]
    return json.loads(blob)


def load_agent_definition(source: Path | None = None, name: str = "Clippy") -> AgentDef:
    folder = source or agent_source_dir(name)
    data = parse_js_object((folder / "agent.js").read_text(encoding="utf-8"), AGENT_JS_RE)
    width, height = data["framesize"]
    return AgentDef(
        name=name,
        overlay_count=int(data.get("overlayCount", 1)),
        frame_size=(int(width), int(height)),
        animations=data["animations"],
        sounds=list(data.get("sounds") or []),
    )


def animation_names(agent: AgentDef) -> list[str]:
    return sorted(agent.animations)


def iter_image_cells(agent: AgentDef) -> Iterator[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    for animation in agent.animations.values():
        for frame in animation.get("frames", []):
            for cell in frame.get("images") or []:
                pair = (int(cell[0]), int(cell[1]))
                if pair not in seen:
                    seen.add(pair)
                    yield pair


def extract_frames(agent: AgentDef | None = None, source: Path | None = None) -> Path:
    agent = agent or load_agent_definition(source)
    folder = source or agent_source_dir(agent.name)
    dest = frame_cache_dir(agent.name)
    marker = dest / "manifest.json"
    sheet_path = folder / "map.png"
    stamp = {
        "sheet": str(sheet_path),
        "mtime": sheet_path.stat().st_mtime,
        "size": sheet_path.stat().st_size,
        "frame": list(agent.frame_size),
    }
    hd_dir = dest.with_name(dest.name + "@4x")
    if marker.exists() and json.loads(marker.read_text()) == stamp and (dest / "0_0.png").exists():
        enhance_dir(dest, hd_dir, UPSCALE)
        hd_rest = hd_dir / "0_0.png"
        write_icon(hd_rest if hd_rest.exists() else dest / "0_0.png")
        return dest

    sheet = Image.open(sheet_path).convert("RGBA")
    fw, fh = agent.frame_size
    for x, y in iter_image_cells(agent):
        cell = sheet.crop((x, y, x + fw, y + fh))
        cell.save(dest / f"{x}_{y}.png")
    # Always keep a rest pose even if unused
    sheet.crop((0, 0, fw, fh)).save(dest / "0_0.png")
    marker.write_text(json.dumps(stamp), encoding="utf-8")
    enhance_dir(dest, hd_dir, UPSCALE)
    hd_rest = hd_dir / "0_0.png"
    write_icon(hd_rest if hd_rest.exists() else dest / "0_0.png")
    return dest


def write_icon(rest_frame: Path) -> Path:
    image = Image.open(rest_frame).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((128, 128))
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(image, ((128 - image.width) // 2, (128 - image.height) // 2), image)
    dest = cache_dir() / "clippy.png"
    canvas.save(dest)
    for size in (16, 24, 32, 48, 64):
        icon = canvas.copy()
        icon.thumbnail((size, size))
        icon.save(cache_dir() / f"clippy-{size}.png")
    return dest


def extract_sounds(source: Path | None = None, name: str = "Clippy") -> Path:
    folder = source or agent_source_dir(name)
    dest = sound_cache_dir(name)
    dest.mkdir(parents=True, exist_ok=True)
    js_path = folder / "sounds-mp3.js"
    if not js_path.exists():
        return dest
    marker = dest / "manifest.json"
    stamp = {"mtime": js_path.stat().st_mtime, "size": js_path.stat().st_size}
    if marker.exists() and json.loads(marker.read_text()) == stamp:
        return dest
    import base64

    text = js_path.read_text(encoding="utf-8")
    pairs = SOUND_PAIR_RE.findall(text)
    if not pairs:
        try:
            data = parse_js_object(text, SOUNDS_JS_RE)
            pairs = [(str(key), str(uri)) for key, uri in data.items()]
        except json.JSONDecodeError:
            pairs = []
    for key, uri in pairs:
        match = DATA_URI_RE.match(uri)
        if not match:
            continue
        payload = base64.b64decode(match.group(2))
        (dest / f"{key}.mp3").write_bytes(payload)
    marker.write_text(json.dumps(stamp), encoding="utf-8")
    return dest


def ensure_assets(name: str = "Clippy") -> tuple[AgentDef, Path, Path]:
    if name != "Clippy":
        from clippy_xfce.mascots import ensure_custom

        return ensure_custom(name)
    agent = load_agent_definition(name=name)
    frames = extract_frames(agent)
    sounds = extract_sounds(name=name)
    return agent, frames, sounds


def compose_frame(
    frame_dir: Path,
    images: list[list[int]],
    size: tuple[int, int],
    hd: bool = True,
) -> Image.Image:
    hd_dir = Path(frame_dir).with_name(Path(frame_dir).name + "@4x")
    use_hd = hd and (hd_dir / "0_0.png").exists()
    source = hd_dir if use_hd else frame_dir
    factor = UPSCALE if use_hd else 1
    canvas = Image.new("RGBA", (size[0] * factor, size[1] * factor), (0, 0, 0, 0))
    for cell in images or [[0, 0]]:
        path = source / f"{int(cell[0])}_{int(cell[1])}.png"
        if not path.exists():
            path = Path(frame_dir) / f"{int(cell[0])}_{int(cell[1])}.png"
        if not path.exists():
            continue
        layer = Image.open(path).convert("RGBA")
        if layer.size != canvas.size:
            layer = layer.resize(canvas.size, Image.Resampling.NEAREST)
        canvas.alpha_composite(layer)
    return canvas
