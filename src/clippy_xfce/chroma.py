"""Color-key a flat backdrop and un-blend anti-aliased edges."""

from __future__ import annotations

from collections import deque

import numpy as np
from PIL import Image

# Clawd's card is a warm off-white; body is terracotta.
DEFAULT_THRESHOLD = 12.0
FRINGE = 72.0


def key_background(
    image: Image.Image,
    threshold: float = DEFAULT_THRESHOLD,
    fringe: float = FRINGE,
) -> Image.Image:
    """Flood-fill the corner color, then lift leftover backdrop out of the fringe."""
    src = np.asarray(image.convert("RGBA"), dtype=np.float32)
    height, width, _ = src.shape
    rgb = src[..., :3]
    background = rgb[0, 0]
    distance = np.linalg.norm(rgb - background, axis=-1)

    backdrop = _flood_background(distance, threshold)
    out = src.copy()
    out[backdrop, 3] = 0

    # Soft edge: leftover pixels that still contain backdrop get a real alpha.
    nearby = _dilate(backdrop) & ~backdrop
    fringe_pixels = nearby & (distance < fringe)
    if np.any(fringe_pixels):
        alpha = np.clip(distance[fringe_pixels] / max(fringe * 0.55, 1.0), 0.0, 1.0)
        color = rgb[fringe_pixels]
        lifted = background + (color - background) / np.maximum(alpha[..., None], 0.08)
        out[fringe_pixels, :3] = np.clip(lifted, 0, 255)
        out[fringe_pixels, 3] = alpha * 255

    # Anything still almost the card color should not sit on the desktop.
    leftover = ~backdrop & (distance < threshold)
    out[leftover, 3] = 0
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def _flood_background(distance: np.ndarray, threshold: float) -> np.ndarray:
    height, width = distance.shape
    marked = np.zeros((height, width), dtype=bool)
    queue: deque[tuple[int, int]] = deque()

    def consider(y: int, x: int) -> None:
        if 0 <= y < height and 0 <= x < width and not marked[y, x] and distance[y, x] < threshold:
            marked[y, x] = True
            queue.append((y, x))

    for x in range(width):
        consider(0, x)
        consider(height - 1, x)
    for y in range(height):
        consider(y, 0)
        consider(y, width - 1)

    while queue:
        y, x = queue.popleft()
        consider(y - 1, x)
        consider(y + 1, x)
        consider(y, x - 1)
        consider(y, x + 1)
    return marked


def _dilate(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, mode="constant")
    grown = np.zeros_like(mask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= padded[1 + dy : mask.shape[0] + 1 + dy, 1 + dx : mask.shape[1] + 1 + dx]
    return grown


def crop_transparent(image: Image.Image, padding: int = 20) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return image
    cropped = image.crop(bbox)
    width, height = cropped.size
    canvas = Image.new("RGBA", (width + padding * 2, height + padding * 2), (0, 0, 0, 0))
    canvas.paste(cropped, (padding, padding), cropped)
    return canvas
