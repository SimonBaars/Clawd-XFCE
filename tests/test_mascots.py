from clippy_xfce.animator import MOOD_ANIMATIONS
from clippy_xfce.mascots import MASCOT_IDS, ensure_clawd
from clippy_xfce.sprites import compose_frame, ensure_assets


def test_clawd_has_mood_animations(tmp_path, monkeypatch):
    from clippy_xfce import mascots as m
    from clippy_xfce import paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "frame_cache_dir", lambda name="Clawd": tmp_path / "frames")
    monkeypatch.setattr(paths, "sound_cache_dir", lambda name="Clawd": tmp_path / "sounds")
    monkeypatch.setattr(m, "frame_cache_dir", lambda name="Clawd": tmp_path / "frames")
    monkeypatch.setattr(m, "sound_cache_dir", lambda name="Clawd": tmp_path / "sounds")
    monkeypatch.setattr(m, "cache_dir", lambda: tmp_path)
    (tmp_path / "frames").mkdir()
    (tmp_path / "sounds").mkdir()

    agent, frames, _sounds = ensure_clawd()
    assert agent.name == "Clawd"
    assert (frames / "0_0.png").exists()
    rest = compose_frame(frames, [[0, 0]], agent.frame_size, hd=False)
    assert rest.getpixel((0, 0))[3] == 0
    assert rest.getchannel("A").getbbox() is not None
    for names in MOOD_ANIMATIONS.values():
        assert any(name in agent.animations for name in names)


def test_ensure_assets_dispatches():
    assert "Clawd" in MASCOT_IDS
    clippy, *_ = ensure_assets("Clippy")
    assert clippy.name == "Clippy"
