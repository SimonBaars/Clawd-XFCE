from clippy_xfce.desktop import gtk_accel_to_xfce


def test_hotkey_mapping():
    assert gtk_accel_to_xfce("<Ctrl><Alt>c") == "<Primary><Alt>c"
    assert gtk_accel_to_xfce("<Control><Shift>space") == "<Primary><Shift>space"
