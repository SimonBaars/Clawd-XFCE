from clippy_xfce.config import Settings, discover_api_key, load_settings, save_settings


def test_sanitize_unknown_model():
    settings = Settings(model="nope", scale=9, max_tokens=2, confirm_mode="maybe", mascot="bonzi").sanitized()
    assert settings.model == "claude-sonnet-5"
    assert settings.scale == 6.0
    assert Settings(scale=0.2).sanitized().scale == 0.75
    assert settings.max_tokens >= 256
    assert settings.confirm_mode == "destructive"
    assert settings.mascot == "Clippy"
    assert Settings().dodge_mouse is False
    assert Settings().dodge_hold_key == "Shift"
    assert Settings(dodge_hold_key="nope").sanitized().dodge_hold_key == "Shift"


def test_roundtrip(tmp_path, monkeypatch):
    from clippy_xfce import config as cfg

    monkeypatch.setattr(cfg, "config_path", lambda: tmp_path / "config.toml")
    monkeypatch.setattr(cfg, "secrets_path", lambda: tmp_path / "secrets.toml")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings = Settings(model="claude-opus-5", api_key="sk-ant-testkey-12345678901234567890")
    save_settings(settings)
    loaded = load_settings()
    assert loaded.model == "claude-opus-5"
    assert loaded.api_key.endswith("34567890")
    assert (tmp_path / "secrets.toml").stat().st_mode & 0o077 == 0
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_discover_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    assert discover_api_key() == "sk-ant-from-env"


def test_restores_original_size_from_4x_default(tmp_path, monkeypatch):
    from clippy_xfce import config as cfg

    monkeypatch.setattr(cfg, "config_path", lambda: tmp_path / "config.toml")
    monkeypatch.setattr(cfg, "secrets_path", lambda: tmp_path / "secrets.toml")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / "config.toml").write_text("scale = 4.0\nidle_seconds = 12.0\n", encoding="utf-8")
    loaded = load_settings()
    assert loaded.scale == 2.0
    assert loaded.idle_seconds == 6.0
    assert loaded.config_version >= 3
    saved = (tmp_path / "config.toml").read_text()
    assert "scale = 2.0" in saved


def test_keeps_explicit_scale_after_v3(tmp_path, monkeypatch):
    from clippy_xfce import config as cfg

    monkeypatch.setattr(cfg, "config_path", lambda: tmp_path / "config.toml")
    monkeypatch.setattr(cfg, "secrets_path", lambda: tmp_path / "secrets.toml")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    save_settings(Settings(scale=2.5, config_version=3))
    loaded = load_settings()
    assert loaded.scale == 2.5
    assert loaded.config_version >= 3
