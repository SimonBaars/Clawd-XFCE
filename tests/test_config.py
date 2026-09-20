from clippy_xfce.config import Settings, discover_api_key, load_settings, save_settings


def test_sanitize_unknown_model():
    settings = Settings(model="nope", scale=9, max_tokens=2, confirm_mode="maybe").sanitized()
    assert settings.model == "claude-sonnet-5"
    assert settings.scale == 3.0
    assert settings.max_tokens >= 256
    assert settings.confirm_mode == "destructive"


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
