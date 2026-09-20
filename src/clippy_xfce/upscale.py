"""High-quality 4x enhancement for every Clippy sprite cell.

Office Assistant frames are 124x93 with real anti-aliasing. Scale2x/EPX
assumes chunky pixel art and turns those soft curves into stairs. Lanczos
reconstructs the linework at 4x; a light unsharp pass restores the inked
look. Color is resized premultiplied so transparent edges stay clean.
Results are cached next to the extracted cells.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

UPSCALE = 4
ALGO = "lanczos-unsharp-v1"


def enhance_frame(image: Image.Image, factor: int = UPSCALE) -> Image.Image:
    src = image.convert("RGBA")
    target = (src.width * factor, src.height * factor)
    if src.size == target:
        return src
    rgba = _resize_premultiplied(src, target)
    rgb = rgba.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.15, percent=115, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(rgba.getchannel("A"))
    return out


def _resize_premultiplied(image: Image.Image, target: tuple[int, int]) -> Image.Image:
    arr = np.asarray(image, dtype=np.float32)
    alpha = arr[..., 3:4] / 255.0
    arr[..., :3] *= alpha
    premul = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    scaled = premul.resize(target, Image.Resampling.LANCZOS)
    out = np.asarray(scaled, dtype=np.float32)
    a = out[..., 3:4]
    np.divide(out[..., :3], a / 255.0, out=out[..., :3], where=a > 8)
    out[..., :3] = np.clip(out[..., :3], 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def enhance_dir(src_dir: Path, dest_dir: Path, factor: int = UPSCALE) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    marker = dest_dir / "manifest.json"
    sources = sorted(path.name for path in src_dir.glob("*.png"))
    stamp = {"algo": ALGO, "factor": factor, "files": sources}
    if marker.exists() and json.loads(marker.read_text()) == stamp:
        return dest_dir
    for name in sources:
        source = Image.open(src_dir / name)
        enhance_frame(source, factor).save(dest_dir / name)
    marker.write_text(json.dumps(stamp), encoding="utf-8")
    return dest_dir
