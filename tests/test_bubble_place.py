from clippy_xfce.ui.bubble import bubble_anchor


def test_classic_mascot_on_the_right():
    x, side, nudge = bubble_anchor(cx=1400, cw=248, bw=400, work_x=0, work_w=1920)
    assert side == "right"
    assert nudge is None
    assert x == 1400 - 400 - 18


def test_nudges_mascot_to_stay_on_the_right():
    x, side, nudge = bubble_anchor(cx=200, cw=248, bw=400, work_x=0, work_w=1920)
    assert side == "right"
    assert x == 8
    assert nudge == 8 + 400 + 18
