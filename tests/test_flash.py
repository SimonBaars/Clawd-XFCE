from clippy_xfce.ui.flash import caption_text, clamp_seconds


def test_clamp_seconds():
    assert clamp_seconds(5) == 5
    assert clamp_seconds(0) == 2
    assert clamp_seconds(99) == 12
    assert clamp_seconds("nope") == 5


def test_caption_text_is_short():
    assert caption_text("  git init   now  ") == "git init now"
    assert len(caption_text("x" * 800)) == 400
