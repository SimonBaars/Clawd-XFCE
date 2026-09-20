"""Clippy.js-compatible animation player."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

from clippy_xfce.sprites import AgentDef

IDLE_ANIMATIONS = (
    "Idle1_1",
    "IdleAtom",
    "IdleEyeBrowRaise",
    "IdleFingerTap",
    "IdleHeadScratch",
    "IdleRopePile",
    "IdleSideToSide",
    "IdleSnooze",
    "LookLeft",
    "LookRight",
    "LookUp",
    "LookDown",
    "LookUpLeft",
    "LookUpRight",
    "LookDownLeft",
    "LookDownRight",
)

MOOD_ANIMATIONS = {
    "idle": IDLE_ANIMATIONS,
    "greet": ("Greeting", "Wave", "Show"),
    "think": ("Thinking", "Processing", "Searching"),
    "search": ("Searching", "CheckingSomething", "Hearing_1"),
    "write": ("Writing", "Print", "Save"),
    "talk": ("Explain", "GestureRight", "GestureUp"),
    "act": ("GetTechy", "Processing", "Searching"),
    "success": ("Congratulate", "GetArtsy", "Wave"),
    "error": ("Alert", "GetAttention", "CheckingSomething"),
    "bye": ("GoodBye", "Hide"),
    "rest": ("RestPose",),
}


@dataclass
class FrameView:
    animation: str
    index: int
    images: list[list[int]]
    duration_ms: int
    sound: str | None = None


@dataclass
class Animator:
    agent: AgentDef
    current: str = "RestPose"
    index: int = 0
    exiting: bool = False
    queue: list[str] = field(default_factory=list)
    on_sound: Callable[[str], None] | None = None

    def animations(self) -> list[str]:
        return sorted(self.agent.animations)

    def has(self, name: str) -> bool:
        return name in self.agent.animations

    def play(self, name: str, interrupt: bool = False) -> None:
        if not self.has(name):
            return
        if interrupt or self.current in ("RestPose", "") or not self._frames():
            self._start(name)
            return
        if name not in self.queue:
            self.queue.append(name)

    def play_mood(self, mood: str, interrupt: bool = False) -> str:
        options = [name for name in MOOD_ANIMATIONS.get(mood, ()) if self.has(name)]
        if not options:
            options = [name for name in IDLE_ANIMATIONS if self.has(name)]
        name = random.choice(options) if options else "RestPose"
        self.play(name, interrupt=interrupt)
        return name

    def stop(self) -> None:
        self.exiting = True
        self.queue.clear()

    def idle(self) -> str:
        return self.play_mood("idle", interrupt=False)

    def _start(self, name: str) -> None:
        self.current = name
        self.index = 0
        self.exiting = False

    def _frames(self) -> list[dict[str, Any]]:
        animation = self.agent.animations.get(self.current) or {}
        return list(animation.get("frames") or [])

    def current_view(self) -> FrameView:
        frames = self._frames()
        if not frames:
            return FrameView("RestPose", 0, [[0, 0]], 250)
        frame = frames[min(self.index, len(frames) - 1)]
        return FrameView(
            animation=self.current,
            index=self.index,
            images=list(frame.get("images") or [[0, 0]]),
            duration_ms=max(10, int(frame.get("duration") or 100)),
            sound=str(frame["sound"]) if frame.get("sound") is not None else None,
        )

    def advance(self) -> FrameView:
        frames = self._frames()
        if not frames:
            return self.current_view()

        frame = frames[min(self.index, len(frames) - 1)]
        if self.exiting and "exitBranch" in frame:
            self.index = int(frame["exitBranch"])
            self.exiting = False
            return self.current_view()

        branched = False
        branching = frame.get("branching") or {}
        branches = branching.get("branches") or []
        if branches and not self.exiting:
            roll = random.random() * 100
            for branch in branches:
                weight = float(branch.get("weight") or 0)
                if roll <= weight:
                    self.index = int(branch.get("frameIndex") or 0)
                    branched = True
                    break
                roll -= weight

        if not branched:
            self.index += 1
            if self.index >= len(frames):
                if self.queue:
                    self._start(self.queue.pop(0))
                else:
                    self._start("RestPose")
        return self.current_view()
