from clippy_xfce.agent.claude import _describe, _persistable, _should_fallback, _tool_result, strip_old_images
from clippy_xfce.agent.prompts import computer_tools, system_prompt


def test_prompt_contains_personality():
    text = system_prompt("memories here", "desktop here")
    assert "Clippy" in text
    assert "memories here" in text
    assert "desktop here" in text


def test_tool_declarations():
    tools = computer_tools("toolset", True, True, True)
    types = [tool.get("type") or tool.get("name") for tool in tools]
    assert "computer_toolset_20260801" in types
    assert "bash_20250124" in types
    assert any(tool.get("name") == "remember" for tool in tools)
    legacy = computer_tools("legacy", True, False, False)
    assert legacy[0]["type"] == "computer_20251124"


def test_strip_images_keeps_latest():
    def img():
        return {"type": "image", "source": {"type": "base64", "data": "xx"}}

    messages = [
        {"role": "user", "content": [img(), {"type": "text", "text": "one"}]},
        {"role": "user", "content": [img(), {"type": "text", "text": "two"}]},
        {"role": "user", "content": [img(), {"type": "text", "text": "three"}]},
    ]
    cleaned = strip_old_images(messages, keep=1)
    images = 0
    omitted = 0
    for message in cleaned:
        for block in message["content"]:
            if block.get("type") == "image":
                images += 1
            if "omitted" in str(block.get("text", "")):
                omitted += 1
    assert images == 1
    assert omitted == 2


def test_tool_result_and_fallback():
    result = _tool_result("abc", "OK", "computer")
    assert result["toolset_name"] == "computer"
    assert result["tool_use_id"] == "abc"
    err = _tool_result("abc", "nope", "computer", error=True)
    assert err["is_error"] is True
    assert _should_fallback("model does not support computer_toolset_20260801")
    summary, danger = _describe("bash", {"command": "rm -rf /tmp/x"}, False)
    assert "rm" in summary and danger
    persisted = _persistable([{"type": "image", "source": {}}, {"type": "text", "text": "hi"}])
    assert persisted[0]["text"] == "[screenshot]"
