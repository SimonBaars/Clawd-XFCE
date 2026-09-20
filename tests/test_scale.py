from clippy_xfce.agent.scale import ScreenScaler


def test_no_scale_for_1080p():
    scaler = ScreenScaler(1920, 1200, max_long_edge=2576)
    assert scaler.factor == 1.0
    assert scaler.shot_size == (1920, 1200)
    assert scaler.to_screen(100, 50) == (100, 50)
    assert scaler.to_shot(100, 50) == (100, 50)


def test_downscale_and_roundtrip():
    scaler = ScreenScaler(3840, 2160, max_long_edge=1568)
    assert scaler.factor < 1
    shot_w, shot_h = scaler.shot_size
    assert max(shot_w, shot_h) <= 1568
    x, y = scaler.to_screen(shot_w / 2, shot_h / 2)
    assert abs(x - 1920) < 3
    assert abs(y - 1080) < 3
    region = scaler.region_to_screen([10, 20, 200, 80])
    assert region[2] > region[0]
    assert region[3] > region[1]
