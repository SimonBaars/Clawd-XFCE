"""User settings and API-key discovery."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from clippy_xfce.mascots import MASCOT_IDS
from clippy_xfce.paths import config_path, secrets_path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def _dump_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
        elif value is None:
            continue
        else:
            escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{escaped}"')
    return "\n".join(lines) + "\n"


MODELS = (
    "claude-sonnet-5",
    "claude-opus-5",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
)

TOOL_MODES = ("toolset", "legacy")
CONFIRM_MODES = ("destructive", "always", "never")
SCREENSHOT_MODES = ("always", "ask", "never")


@dataclass
class Settings:
    model: str = "claude-sonnet-5"
    max_tokens: int = 4096
    max_iterations: int = 24
    computer_use: bool = True
    bash_tool: bool = True
    editor_tool: bool = True
    tool_mode: str = "toolset"
    confirm_mode: str = "destructive"
    screenshot_mode: str = "always"
    hide_self_in_screenshots: bool = True
    sounds: bool = True
    scale: float = 2.0
    pos_x: int = -1
    pos_y: int = -1
    start_hidden: bool = False
    autostart: bool = False
    proactive_greeting: bool = True
    max_screenshot_edge: int = 2576
    keep_screenshots: int = 8
    idle_seconds: float = 6.0
    hotkey: str = "<Ctrl><Alt>c"
    mascot: str = "Clippy"
    config_version: int = 3
    api_key: str = ""

    def sanitized(self) -> "Settings":
        copy = Settings(**asdict(self))
        if copy.model not in MODELS:
            copy.model = MODELS[0]
        if copy.tool_mode not in TOOL_MODES:
            copy.tool_mode = "toolset"
        if copy.confirm_mode not in CONFIRM_MODES:
            copy.confirm_mode = "destructive"
        if copy.screenshot_mode not in SCREENSHOT_MODES:
            copy.screenshot_mode = "always"
        if copy.mascot not in MASCOT_IDS:
            copy.mascot = "Clippy"
        copy.scale = min(6.0, max(0.75, float(copy.scale)))
        copy.max_tokens = min(16000, max(256, int(copy.max_tokens)))
        copy.max_iterations = min(60, max(1, int(copy.max_iterations)))
        copy.idle_seconds = min(60.0, max(2.0, float(copy.idle_seconds)))
        copy.config_version = max(1, int(copy.config_version or 1))
        return copy


_KEY_RE = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _write_toml(path: Path, data: dict[str, Any], private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_toml(data), encoding="utf-8")
    if private:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def discover_api_key() -> str:
    env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env:
        return env
    secrets = _read_toml(secrets_path())
    stored = str(secrets.get("api_key", "")).strip()
    if stored:
        return stored
    candidates = [
        Path.home() / ".bashrc-personal",
        Path.home() / ".bashrc",
        Path.home() / ".profile",
        Path.home() / ".claude" / "settings.tmp.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = _KEY_RE.search(text)
        if match:
            return match.group(0)
    return ""


def load_settings() -> Settings:
    raw = _read_toml(config_path())
    known = {item.name for item in fields(Settings)}
    values = {key: value for key, value in raw.items() if key in known and key != "api_key"}
    version = int(values.get("config_version") or 1)
    migrated = False
    if version < 2 and values.get("idle_seconds") == 12.0:
        values["idle_seconds"] = 6.0
        migrated = True
    if version < 3 and values.get("scale") == 4.0:
        # HD frames stay 4x; the on-screen mascot goes back to the original size.
        values["scale"] = 2.0
        migrated = True
    values["config_version"] = max(version, 3)
    settings = Settings(**values).sanitized()
    settings.api_key = discover_api_key()
    if migrated and config_path().exists():
        save_settings(settings)
    return settings


def save_settings(settings: Settings) -> None:
    settings = settings.sanitized()
    payload = asdict(settings)
    api_key = payload.pop("api_key")
    _write_toml(config_path(), payload)
    if api_key:
        _write_toml(secrets_path(), {"api_key": api_key}, private=True)
        os.environ["ANTHROPIC_API_KEY"] = api_key
