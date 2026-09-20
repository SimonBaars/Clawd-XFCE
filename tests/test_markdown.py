from clippy_xfce.markdown import to_pango


def test_plain_text_is_escaped():
    assert to_pango("a < b & c > d") == "a &lt; b &amp; c &gt; d"


def test_simple_markdown():
    assert "<b>bold</b>" in to_pango("say **bold** now")
    assert "<i>hi</i>" in to_pango("say *hi* now")
    assert "<tt>git init</tt>" in to_pango("run `git init`")
    assert "<s>old</s>" in to_pango("~~old~~")
    assert to_pango("- first\n- second") == "• first\n• second"
    assert to_pango("# Title") == "<b>Title</b>"


def test_link_and_code_fence():
    markup = to_pango("see [docs](https://example.com/a?x=1&y=2)")
    assert 'href="https://example.com/a?x=1&amp;y=2"' in markup
    assert to_pango("[nope](javascript:alert(1))") == "nope"
    assert "<tt>echo hi</tt>" in to_pango("```\necho hi\n```")


def test_code_and_snake_case_are_left_alone():
    assert "<i>" not in to_pango("use file_name later")
    assert to_pango("use `**still**`") == "use <tt>**still**</tt>"
