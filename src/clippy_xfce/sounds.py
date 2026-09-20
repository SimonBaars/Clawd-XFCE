"""Play classic Clippy animation sounds."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from clippy_xfce.sprites import extract_sounds


class SoundPlayer:
    def __init__(self, enabled: bool = True, agent: str = "Clippy") -> None:
        self.enabled = enabled
        self.agent = agent
        self._dir: Path | None = None
        self._player = next(
            (name for name in ("paplay", "ffplay", "gst-play-1.0", "mpv") if shutil.which(name)),
            None,
        )

    def prepare(self) -> None:
        self._dir = extract_sounds(name=self.agent)

    def play(self, sound_id: str) -> None:
        if not self.enabled or not self._player:
            return
        if self._dir is None:
            self.prepare()
        assert self._dir is not None
        path = self._dir / f"{sound_id}.mp3"
        if not path.exists():
            return
        cmd = [self._player, str(path)]
        if self._player == "ffplay":
            cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
        elif self._player == "mpv":
            cmd = ["mpv", "--no-video", "--really-quiet", str(path)]
        elif self._player == "gst-play-1.0":
            cmd = ["gst-play-1.0", "--no-interactive", str(path)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
