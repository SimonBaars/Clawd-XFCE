"""Simple Markdown → Pango markup for speech-bubble labels."""

from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:\w*)\n?(.*?)```", re.S)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_ITALIC_STAR = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ITALIC_UNDER = re.compile(r"(?<![A-Za-z0-9_])_(?!_)(.+?)(?<!_)_(?![A-Za-z0-9_])")
_STRIKE = re.compile(r"~~(.+?)~~")
_HEADING = re.compile(r"(?m)^#{1,6}\s+(.+)$")
_UL = re.compile(r"(?m)^\s*[-*]\s+")
_SAFE_URL = re.compile(r"^(https?://|mailto:)", re.I)
_STASH = re.compile(r"\x00(\d+)\x00")


def escape_pango(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(text: str) -> str:
    # Caller already ran escape_pango on the whole string.
    return text.replace('"', "&quot;")


def to_pango(text: str) -> str:
    """Render a small Markdown subset as Pango markup."""
    if not text:
        return ""
    stashed: list[str] = []

    def hold(inner: str) -> str:
        stashed.append(inner)
        return f"\x00{len(stashed) - 1}\x00"

    text = _FENCE.sub(lambda match: hold(escape_pango(match.group(1).strip("\n"))), text)
    text = _INLINE_CODE.sub(lambda match: hold(escape_pango(match.group(1))), text)
    text = escape_pango(text)

    def link(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if _SAFE_URL.match(url):
            return f'<a href="{_escape_attr(url)}">{label}</a>'
        return label

    text = _LINK.sub(link, text)
    text = _BOLD.sub(lambda match: f"<b>{match.group(1) or match.group(2)}</b>", text)
    text = _ITALIC_STAR.sub(r"<i>\1</i>", text)
    text = _ITALIC_UNDER.sub(r"<i>\1</i>", text)
    text = _STRIKE.sub(r"<s>\1</s>", text)
    text = _HEADING.sub(r"<b>\1</b>", text)
    text = _UL.sub("• ", text)
    text = _STASH.sub(
        lambda match: (
            f'<span bgcolor="#3a332f" fgcolor="#eee3da"><tt>'
            f"{stashed[int(match.group(1))]}</tt></span>"
        ),
        text,
    )
    return text
