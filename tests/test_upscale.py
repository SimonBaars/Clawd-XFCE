from PIL import Image

from clippy_xfce.upscale import ALGO, enhance_dir, enhance_frame


def test_enhance_frame_is_4x_and_keeps_color():
    src = Image.new("RGBA", (10, 6), (0, 0, 0, 0))
    src.putpixel((4, 3), (220, 40, 40, 255))
    out = enhance_frame(src, 4)
    assert out.size == (40, 24)
    pixel = out.getpixel((17, 13))
    assert pixel[0] > 150
    assert pixel[3] > 150


def test_enhance_dir_caches_by_algo(tmp_path):
    src = tmp_path / "in"
    dest = tmp_path / "out"
    src.mkdir()
    Image.new("RGBA", (4, 4), (9, 9, 9, 255)).save(src / "0_0.png")
    enhance_dir(src, dest, 4)
    assert (dest / "0_0.png").exists()
    assert Image.open(dest / "0_0.png").size == (16, 16)
    first = (dest / "0_0.png").read_bytes()
    enhance_dir(src, dest, 4)
    assert (dest / "0_0.png").read_bytes() == first
    stamp = (dest / "manifest.json").read_text()
    assert ALGO in stamp
