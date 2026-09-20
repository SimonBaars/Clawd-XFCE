from pathlib import Path

from clippy_xfce.sprites import (
    animation_names,
    ensure_assets,
    extract_frames,
    iter_image_cells,
    load_agent_definition,
    parse_js_object,
    AGENT_JS_RE,
)


def test_parse_and_list_animations():
    agent = load_agent_definition()
    names = animation_names(agent)
    assert agent.frame_size == (124, 93)
    for expected in (
        "Greeting",
        "Wave",
        "Writing",
        "Searching",
        "Congratulate",
        "IdleRopePile",
        "GetAttention",
        "RestPose",
    ):
        assert expected in names
    assert len(names) >= 40
    cells = list(iter_image_cells(agent))
    assert (0, 0) in cells
    assert len(cells) > 50


def test_extract_frames(tmp_path, monkeypatch):
    from clippy_xfce import paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "frame_cache_dir", lambda name="Clippy": tmp_path / "frames")
    (tmp_path / "frames").mkdir()
    dest = extract_frames()
    assert (dest / "0_0.png").exists()
    assert (dest / "manifest.json").exists()


def test_ensure_assets(tmp_path, monkeypatch):
    from clippy_xfce import paths, sprites

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "frame_cache_dir", lambda name="Clippy": tmp_path / "frames")
    monkeypatch.setattr(paths, "sound_cache_dir", lambda name="Clippy": tmp_path / "sounds")
    monkeypatch.setattr(sprites, "frame_cache_dir", lambda name="Clippy": tmp_path / "frames")
    monkeypatch.setattr(sprites, "sound_cache_dir", lambda name="Clippy": tmp_path / "sounds")
    monkeypatch.setattr(sprites, "cache_dir", lambda: tmp_path)
    (tmp_path / "frames").mkdir()
    (tmp_path / "sounds").mkdir()
    agent, frames, sounds = ensure_assets()
    assert agent.name == "Clippy"
    assert (frames / "0_0.png").exists()
    assert list(Path(sounds).glob("*.mp3"))


def test_js_object_helper():
    text = "clippy.ready('Clippy', {\"overlayCount\": 1, \"framesize\": [124, 93]});"
    data = parse_js_object(text, AGENT_JS_RE)
    assert data["framesize"] == [124, 93]
