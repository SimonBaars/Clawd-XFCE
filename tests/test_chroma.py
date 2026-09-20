from PIL import Image

from clippy_xfce.chroma import crop_transparent, key_background
from clippy_xfce.mascots import clawd_source


def test_keys_flat_card_and_keeps_body():
    keyed = key_background(Image.open(clawd_source()))
    assert keyed.mode == "RGBA"
    assert keyed.getpixel((0, 0))[3] == 0
    assert keyed.getpixel((keyed.width - 1, 0))[3] == 0
    cx, cy = keyed.width // 2, keyed.height // 2
    body = keyed.getpixel((cx, cy))
    assert body[3] > 200
    assert body[0] > 150 and body[1] < 160


def test_crop_keeps_padding_and_alpha():
    keyed = key_background(Image.open(clawd_source()))
    cropped = crop_transparent(keyed, padding=12)
    assert cropped.size[0] > 12 * 2
    assert cropped.getpixel((0, 0))[3] == 0
    assert cropped.getchannel("A").getbbox() is not None
