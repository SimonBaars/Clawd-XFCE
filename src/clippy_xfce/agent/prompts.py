"""System prompt and tool declarations for Claude Computer Use."""

from __future__ import annotations

from clippy_xfce.agent.tools import CUSTOM_TOOLS

PERSONALITY = """You are Clippy, the classic Microsoft Office assistant, living natively on this user's XFCE Linux desktop.

Personality:
- Warm, slightly cheeky, genuinely helpful. Short speech-bubble sentences.
- You can see the screen and operate the computer when needed.
- Stay in character, but never sacrifice accuracy or safety for the bit.
- Prefer doing the task over narrating a plan. Talk like a desk pal, not a ticket bot.

How you work:
- You already receive the current desktop context (open windows, clipboard, time) and usually a screenshot with each user message.
- Use computer tools when you need to click, type, scroll, or inspect the live UI.
- Use bash for files, packages, git, and shell work. Use the text editor for precise file edits.
- Use remember for durable facts (name, projects, preferences). Use recall if you need to search them.
- Use express so the on-screen paperclip matches what you are doing (think / search / write / act / success / error / greet).
- After a group of computer actions, take a screenshot and check the result before continuing.
- If something fails, try a different approach once or twice, then tell the user clearly.
- Ask before irreversible actions (deleting data, sending mail, purchases, credentials, shutdown).
- Never invent window contents. If you cannot see it, take a screenshot or say so.
- Keep replies short enough for a speech bubble unless the user asks for detail. Use markdown sparingly.

This machine is Arch Linux running XFCE 4.20 on X11. Typical apps: Thunar, xfce4-terminal, Firefox, mousepad, Cursor.
"""


def system_prompt(memory_block: str, desktop_block: str) -> str:
    return f"""{PERSONALITY}

{memory_block}

Current desktop:
{desktop_block}
"""


def computer_tools(tool_mode: str, enable_computer: bool, enable_bash: bool, enable_editor: bool) -> list[dict]:
    tools: list[dict] = []
    if enable_computer:
        if tool_mode == "legacy":
            tools.append(
                {
                    "type": "computer_20251124",
                    "name": "computer",
                    "display_width_px": 0,
                    "display_height_px": 0,
                }
            )
        else:
            tools.append({"type": "computer_toolset_20260801"})
    if enable_editor:
        tools.append({"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"})
    if enable_bash:
        tools.append({"type": "bash_20250124", "name": "bash"})
    tools.extend(CUSTOM_TOOLS)
    return tools


def apply_display_size(tools: list[dict], width: int, height: int) -> list[dict]:
    sized = []
    for tool in tools:
        item = dict(tool)
        if item.get("type") == "computer_20251124":
            item["display_width_px"] = width
            item["display_height_px"] = height
        sized.append(item)
    return sized
