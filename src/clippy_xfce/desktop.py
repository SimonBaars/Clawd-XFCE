"""XFCE desktop / autostart / icon integration."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from clippy_xfce.paths import cache_dir, package_data

DESKTOP = """[Desktop Entry]
Type=Application
Name=Clippy
Comment=Native XFCE assistant powered by Claude Computer Use
Exec={exec}
Icon={icon}
Terminal=false
Categories=Utility;GTK;Office;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


def app_command() -> str:
    here = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "clippy"
    if here.exists():
        return str(here)
    clippy = shutil.which("clippy")
    if clippy:
        return clippy
    return "python3 -m clippy_xfce"


def install_desktop_files(autostart: bool, icon: Path | None = None) -> None:
    icon_file = icon or (cache_dir() / "clippy.png")
    applications = Path.home() / ".local/share/applications"
    applications.mkdir(parents=True, exist_ok=True)
    text = DESKTOP.format(exec=app_command(), icon=icon_file)
    (applications / "clippy.desktop").write_text(text, encoding="utf-8")
    auto_dir = Path.home() / ".config/autostart"
    auto_dir.mkdir(parents=True, exist_ok=True)
    auto_path = auto_dir / "clippy.desktop"
    if autostart:
        auto_path.write_text(text, encoding="utf-8")
    elif auto_path.exists():
        auto_path.unlink()
    icons = Path.home() / ".local/share/icons/hicolor/128x128/apps"
    icons.mkdir(parents=True, exist_ok=True)
    if icon_file.exists():
        shutil.copy2(icon_file, icons / "clippy.png")
    bundled = package_data() / "icons" / "clippy.svg"
    if bundled.exists():
        svg_dir = Path.home() / ".local/share/icons/hicolor/scalable/apps"
        svg_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled, svg_dir / "clippy.svg")
    os.system("update-desktop-database ~/.local/share/applications >/dev/null 2>&1")
