#!/usr/bin/env python3
"""Re-download the official clippy.js Clippy sprite sheet, animations, and sounds."""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src/clippy_xfce/data/agents/Clippy"
BASE = "https://cdn.jsdelivr.net/gh/sagudev/clippyjs@2.1.0/agents/Clippy"

FILES = ("agent.js", "map.png", "sounds-mp3.js")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        url = f"{BASE}/{name}"
        dest = DEST / name
        print(f"fetch {url}")
        with urllib.request.urlopen(url) as response:
            dest.write_bytes(response.read())
        print(f"  wrote {dest} ({dest.stat().st_size} bytes)")
    print("done")


if __name__ == "__main__":
    main()
