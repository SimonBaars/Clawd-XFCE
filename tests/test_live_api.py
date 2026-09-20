import os

import pytest


def _live_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key.startswith("sk-ant-") and "testkey" not in key:
        return key
    return ""


@pytest.mark.skipif(not _live_key(), reason="needs ANTHROPIC_API_KEY")
def test_plain_hello_roundtrip():
    import anthropic

    client = anthropic.Anthropic(api_key=_live_key())
    response = client.messages.create(
        model=os.environ.get("CLIPPY_MODEL", "claude-sonnet-5"),
        max_tokens=80,
        messages=[{"role": "user", "content": "Reply with exactly: It looks like you're testing Clippy."}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    assert "Clippy" in text
