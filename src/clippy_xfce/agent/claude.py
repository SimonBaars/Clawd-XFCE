"""Claude Computer Use agent loop."""

from __future__ import annotations

import base64
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from clippy_xfce.agent.computer import ComputerUse
from clippy_xfce.agent.context import context_text, desktop_snapshot
from clippy_xfce.agent.memory import MemoryStore, first_text
from clippy_xfce.agent.prompts import apply_display_size, computer_tools, system_prompt
from clippy_xfce.agent.tools import ToolHub, is_dangerous_bash
from clippy_xfce.config import Settings

COMPUTER_MEMBERS = {
    "screenshot",
    "zoom",
    "left_click",
    "right_click",
    "middle_click",
    "double_click",
    "triple_click",
    "left_click_drag",
    "mouse_move",
    "left_mouse_down",
    "left_mouse_up",
    "cursor_position",
    "scroll",
    "type",
    "key",
    "hold_key",
    "wait",
    "computer",
}

SKIPPED = "Not executed: an earlier computer action in this turn failed."


@dataclass
class AgentEvent:
    kind: str
    text: str = ""
    animation: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


ConfirmFn = Callable[[str, bool], bool]
EmitFn = Callable[[AgentEvent], None]


def _block_to_dict(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    if hasattr(block, "model_dump"):
        return block.model_dump()
    payload: dict[str, Any] = {"type": getattr(block, "type", "text")}
    if payload["type"] == "text":
        payload["text"] = getattr(block, "text", "")
    elif payload["type"] == "tool_use":
        payload["id"] = getattr(block, "id", "")
        payload["name"] = getattr(block, "name", "")
        payload["input"] = getattr(block, "input", {}) or {}
        extra = getattr(block, "toolset_name", None)
        if extra:
            payload["toolset_name"] = extra
    return payload


def _content_list(content: Any) -> list[Any]:
    if content is None:
        return []
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return [content]


def strip_old_images(messages: list[dict[str, Any]], keep: int) -> list[dict[str, Any]]:
    images: list[tuple[int, int]] = []
    for mi, message in enumerate(messages):
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for bi, block in enumerate(content):
            if isinstance(block, dict) and block.get("type") == "image":
                images.append((mi, bi))
            elif (
                isinstance(block, dict)
                and block.get("type") == "tool_result"
                and isinstance(block.get("content"), list)
            ):
                for ci, child in enumerate(block["content"]):
                    if isinstance(child, dict) and child.get("type") == "image":
                        images.append((mi, bi))
    drop = set(images[:-keep]) if keep >= 0 else set()
    cleaned: list[dict[str, Any]] = []
    for mi, message in enumerate(messages):
        content = message.get("content")
        if not isinstance(content, list):
            cleaned.append(message)
            continue
        new_blocks = []
        for bi, block in enumerate(content):
            if (mi, bi) in drop and isinstance(block, dict):
                if block.get("type") == "image":
                    new_blocks.append({"type": "text", "text": "[older screenshot omitted]"})
                    continue
                if block.get("type") == "tool_result":
                    clone = dict(block)
                    clone["content"] = [{"type": "text", "text": "[older screenshot omitted]"}]
                    new_blocks.append(clone)
                    continue
            new_blocks.append(block)
        cleaned.append({**message, "content": new_blocks})
    return cleaned


def image_block(png: bytes) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(png).decode("ascii"),
        },
    }


class ClippyAgent:
    def __init__(
        self,
        settings: Settings,
        memory: MemoryStore,
        computer: ComputerUse,
        tools: ToolHub,
        emit: EmitFn | None = None,
        confirm: ConfirmFn | None = None,
    ) -> None:
        self.settings = settings
        self.memory = memory
        self.computer = computer
        self.tools = tools
        self.emit = emit or (lambda event: None)
        self.confirm = confirm or (lambda _summary, _danger: True)
        self.cancel = threading.Event()
        self.computer_paused = False
        self.conversation_id: int | None = None
        self.messages: list[dict[str, Any]] = []
        self._client = None
        self.tool_mode = settings.tool_mode

    def _client_for(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.settings.api_key or None)
        return self._client

    def new_conversation(self) -> int:
        convo = self.memory.create_conversation()
        self.conversation_id = convo.id
        self.messages = []
        return convo.id

    def load_conversation(self, conversation_id: int) -> None:
        self.conversation_id = conversation_id
        self.messages = self.memory.messages(conversation_id)

    def stop(self) -> None:
        self.cancel.set()

    def _emit(self, kind: str, text: str = "", **data: Any) -> None:
        self.emit(AgentEvent(kind=kind, text=text, data=data))

    def _maybe_screenshot(self) -> bytes | None:
        if not self.settings.computer_use:
            return None
        if self.settings.screenshot_mode != "always":
            return None
        try:
            return self.computer.screenshot_png(hide=False)
        except Exception as exc:
            self._emit("warn", f"Could not capture the screen: {exc}")
            return None

    def _user_content(self, text: str, attach_shot: bool) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = [
            {"type": "text", "text": text},
            {"type": "text", "text": "Desktop now:\n" + context_text(desktop_snapshot())},
        ]
        if attach_shot:
            png = self._maybe_screenshot()
            if png:
                blocks.append(image_block(png))
        return blocks

    def ask(self, text: str) -> str:
        self.cancel.clear()
        if self.conversation_id is None:
            self.new_conversation()
        content = self._user_content(text, attach_shot=True)
        self._append("user", content)
        return self._loop()

    def _append(self, role: str, content: Any) -> None:
        message = {"role": role, "content": content}
        self.messages.append(message)
        if self.conversation_id is not None:
            self.memory.add_message(self.conversation_id, role, _persistable(content))

    def _system(self) -> str:
        return system_prompt(
            self.memory.context_block(self.conversation_id),
            context_text(),
        )

    def _tools(self) -> list[dict[str, Any]]:
        width, height = self.computer.scaler.shot_size
        return apply_display_size(
            computer_tools(
                self.tool_mode,
                self.settings.computer_use,
                self.settings.bash_tool,
                self.settings.editor_tool,
            ),
            width,
            height,
        )

    def _create(self, tools: list[dict[str, Any]]):
        client = self._client_for()
        kwargs: dict[str, Any] = {
            "model": self.settings.model,
            "max_tokens": self.settings.max_tokens,
            "system": self._system(),
            "tools": tools,
            "messages": strip_old_images(self.messages, self.settings.keep_screenshots),
        }
        if self.tool_mode == "legacy":
            return client.beta.messages.create(betas=["computer-use-2025-11-24"], **kwargs)
        return client.messages.create(**kwargs)

    def _loop(self) -> str:
        last_text = ""
        limit = self.settings.max_iterations
        step = 0
        while True:
            if limit and step >= limit:
                self._emit("warn", "I ran out of steps before finishing.")
                return last_text or "I ran out of steps before finishing."
            step += 1
            if self.cancel.is_set():
                self._emit("stopped", "Stopped.")
                return last_text or "Stopped."
            tools = self._tools()
            try:
                response = self._create(tools)
            except Exception as exc:
                message = str(exc)
                if self.tool_mode != "legacy" and _should_fallback(message):
                    self.tool_mode = "legacy"
                    self._emit("status", "Switching to the earlier computer-use tool.")
                    continue
                self._emit("error", message)
                raise
            blocks = [_block_to_dict(block) for block in response.content]
            self._append("assistant", blocks)
            texts = [block.get("text", "") for block in blocks if block.get("type") == "text"]
            last_text = "\n".join(part for part in texts if part).strip()
            if last_text:
                self._emit("assistant", last_text)
            tool_uses = [block for block in blocks if block.get("type") == "tool_use"]
            if not tool_uses or getattr(response, "stop_reason", None) != "tool_use":
                self._maybe_summarize()
                return last_text
            results = self._run_tools(tool_uses)
            self._append("user", results)

    def _run_tools(self, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        failed = False
        for call in calls:
            name = call.get("name") or ""
            payload = call.get("input") or {}
            toolset = call.get("toolset_name")
            tool_use_id = call.get("id")
            is_computer = toolset == "computer" or name in COMPUTER_MEMBERS
            if failed and is_computer:
                results.append(_tool_result(tool_use_id, SKIPPED, toolset, error=True))
                continue
            if self.cancel.is_set():
                results.append(_tool_result(tool_use_id, "Cancelled by user.", toolset, error=True))
                failed = True
                continue
            if is_computer and self.computer_paused:
                results.append(
                    _tool_result(
                        tool_use_id,
                        "Computer use is paused. The user will steer you in chat.",
                        toolset,
                        error=True,
                    )
                )
                failed = True
                continue
            try:
                summary, dangerous = _describe(name, payload, is_computer)
                self._emit("tool", summary, tool=name, input=payload)
                if not self.confirm(summary, dangerous):
                    raise PermissionError("User denied this action.")
                if is_computer:
                    body, is_image = self.computer.handle(name, payload)
                    if is_image:
                        results.append(_tool_result(tool_use_id, image_block(body), toolset))
                    else:
                        results.append(_tool_result(tool_use_id, str(body), toolset))
                else:
                    text = self.tools.handle(name, payload)
                    results.append(_tool_result(tool_use_id, text, toolset))
                    if name == "express":
                        self._emit("express", text)
                    if name in {"flash", "notify_user"}:
                        caption = str(payload.get("text") or payload.get("body") or "").strip()
                        if caption:
                            self._emit("flash", caption)
            except Exception as exc:
                failed = is_computer
                results.append(_tool_result(tool_use_id, str(exc), toolset, error=True))
                self._emit("tool_error", str(exc), tool=name)
        if (
            self.settings.computer_use
            and calls
            and not any((c.get("name") in {"screenshot", "zoom"}) or (c.get("input") or {}).get("action") == "screenshot" for c in calls)
            and not failed
        ):
            # Attach a follow-up glance on the last successful computer result.
            last = next((item for item in reversed(results) if not item.get("is_error")), None)
            if last and last.get("toolset_name") == "computer":
                try:
                    png = self.computer.screenshot_png()
                    content = last.get("content")
                    if isinstance(content, list):
                        content.append(image_block(png))
                    else:
                        last["content"] = [
                            {"type": "text", "text": str(content)},
                            image_block(png),
                        ]
                except Exception:
                    pass
        return results

    def _maybe_summarize(self) -> None:
        if self.conversation_id is None:
            return
        convo = self.memory.get_conversation(self.conversation_id)
        if convo and convo.summary:
            return
        texts = []
        for message in self.messages:
            blob = first_text(message.get("content"))
            if blob:
                texts.append(f"{message['role']}: {blob}")
        if texts:
            summary = " | ".join(texts[:4])
            self.memory.set_summary(self.conversation_id, summary[:400])


def _tool_result(tool_use_id: str, content: Any, toolset: str | None, error: bool = False) -> dict[str, Any]:
    if isinstance(content, dict):
        body: Any = [content]
    elif isinstance(content, list):
        body = content
    else:
        body = [{"type": "text", "text": str(content)}]
    result = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": body,
    }
    if toolset:
        result["toolset_name"] = toolset
    if error:
        result["is_error"] = True
        result["content"] = str(content)
    return result


def _describe(name: str, payload: dict[str, Any], is_computer: bool) -> tuple[str, bool]:
    if name == "bash":
        command = str(payload.get("command") or "")
        return f"Run `{command}`", is_dangerous_bash(command)
    if name in {"str_replace_based_edit_tool", "str_replace_editor", "text_editor"}:
        return f"Edit {payload.get('path')}", False
    if is_computer:
        action = payload.get("action") or name
        return f"Computer: {action} {json.dumps(payload)[:120]}", False
    return f"{name}", False


def _should_fallback(message: str) -> bool:
    lowered = message.lower()
    return any(
        needle in lowered
        for needle in (
            "computer_toolset_20260801",
            "not supported",
            "invalid tool",
            "does not support",
            "unknown tool",
        )
    )


def _persistable(content: Any) -> Any:
    if not isinstance(content, list):
        return content
    stored = []
    for block in content:
        if not isinstance(block, dict):
            stored.append(block)
            continue
        if block.get("type") == "image":
            stored.append({"type": "text", "text": "[screenshot]"})
            continue
        if block.get("type") == "tool_result":
            clone = dict(block)
            inner = clone.get("content")
            if isinstance(inner, list):
                clone["content"] = [
                    {"type": "text", "text": "[screenshot]"}
                    if isinstance(child, dict) and child.get("type") == "image"
                    else child
                    for child in inner
                ]
            stored.append(clone)
            continue
        stored.append(block)
    return stored
