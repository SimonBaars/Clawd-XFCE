from clippy_xfce.dodge import (
    CONTROL_MASK,
    SHIFT_MASK,
    flee_position,
    hold_is_down,
    normalize_hold_key,
    pointer_hits,
    skitter_steps,
)


def test_hold_key_defaults_to_shift():
    assert normalize_hold_key("") == "Shift"
    assert normalize_hold_key("<Ctrl>") == "Ctrl"
    assert normalize_hold_key("super") == "Super"
    assert hold_is_down("Shift", SHIFT_MASK)
    assert not hold_is_down("Shift", CONTROL_MASK)
    assert hold_is_down("Ctrl", CONTROL_MASK)


def test_flees_off_the_pointer():
    mx, my = 120, 110
    x, y, w, h = 100, 100, 80, 60
    work = (0, 0, 800, 600)
    assert pointer_hits(mx, my, x, y, w, h, 40)
    nx, ny = flee_position(mx, my, x, y, w, h, work, margin=40, hop=160)
    assert not pointer_hits(mx, my, nx, ny, w, h, 40)
    assert 8 <= nx <= 800 - w - 8
    assert 8 <= ny <= 600 - h - 8


def test_cornered_mascot_still_leaves_the_pointer():
    mx, my = 20, 20
    x, y, w, h = 8, 8, 80, 60
    work = (0, 0, 400, 300)
    nx, ny = flee_position(mx, my, x, y, w, h, work, margin=40, hop=120)
    assert not pointer_hits(mx, my, nx, ny, w, h, 40)


def test_skitter_ends_on_the_target():
    steps = skitter_steps(10, 10, 200, 80, count=6, work=(0, 0, 800, 600), size=(80, 60))
    assert steps[-1] == (200, 80)
    assert len(steps) == 6
