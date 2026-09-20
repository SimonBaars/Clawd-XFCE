"""Map Claude screenshot coordinates onto the real display."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenScaler:
    screen_width: int
    screen_height: int
    max_long_edge: int = 2576
    max_pixels: int = 3_750_000

    @property
    def factor(self) -> float:
        long_edge = max(self.screen_width, self.screen_height)
        area = max(1, self.screen_width * self.screen_height)
        return min(1.0, self.max_long_edge / long_edge, (self.max_pixels / area) ** 0.5)

    @property
    def shot_size(self) -> tuple[int, int]:
        factor = self.factor
        width = max(1, int(round(self.screen_width * factor)))
        height = max(1, int(round(self.screen_height * factor)))
        return width, height

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        shot_w, shot_h = self.shot_size
        sx = int(round(x * self.screen_width / shot_w))
        sy = int(round(y * self.screen_height / shot_h))
        return clamp(sx, 0, self.screen_width - 1), clamp(sy, 0, self.screen_height - 1)

    def to_shot(self, x: float, y: float) -> tuple[int, int]:
        shot_w, shot_h = self.shot_size
        sx = int(round(x * shot_w / self.screen_width))
        sy = int(round(y * shot_h / self.screen_height))
        return clamp(sx, 0, shot_w - 1), clamp(sy, 0, shot_h - 1)

    def region_to_screen(self, region: list[int] | tuple[int, ...]) -> tuple[int, int, int, int]:
        x0, y0 = self.to_screen(region[0], region[1])
        x1, y1 = self.to_screen(region[2], region[3])
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
