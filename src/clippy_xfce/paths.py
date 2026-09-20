"""XDG and packaged-data locations."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "clippy"


def _xdg(env: str, default: str) -> Path:
    root = Path(os.environ.get(env, Path.home() / default))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    return _xdg("XDG_CONFIG_HOME", ".config")


def data_dir() -> Path:
    return _xdg("XDG_DATA_HOME", ".local/share")


def cache_dir() -> Path:
    return _xdg("XDG_CACHE_HOME", ".cache")


def state_dir() -> Path:
    return _xdg("XDG_STATE_HOME", ".local/state")


def package_data() -> Path:
    return Path(__file__).resolve().parent / "data"


def agent_source_dir(name: str = "Clippy") -> Path:
    return package_data() / "agents" / name


def frame_cache_dir(name: str = "Clippy") -> Path:
    path = cache_dir() / "frames" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def hd_frame_dir(name: str = "Clippy") -> Path:
    path = cache_dir() / "frames" / f"{name}@4x"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sound_cache_dir(name: str = "Clippy") -> Path:
    path = cache_dir() / "sounds" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.toml"


def secrets_path() -> Path:
    return config_dir() / "secrets.toml"


def db_path() -> Path:
    return data_dir() / "memory.db"


def icon_path() -> Path:
    generated = cache_dir() / "clippy.png"
    if generated.exists():
        return generated
    bundled = package_data() / "icons" / "clippy.png"
    return bundled
