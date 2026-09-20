"""Always-on-top animated Clippy overlay."""

from __future__ import annotations

import io
import random
from collections.abc import Callable

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk
from PIL import Image

from clippy_xfce.animator import Animator
from clippy_xfce.dodge import flee_position, hold_is_down, normalize_hold_key, pointer_hits, skitter_steps
from clippy_xfce.sounds import SoundPlayer
from clippy_xfce.sprites import AgentDef, compose_frame


def _pixbuf(image: Image.Image) -> GdkPixbuf.Pixbuf:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(buf.getvalue())
    loader.close()
    return loader.get_pixbuf()


class CharacterWindow(Gtk.Window):
    def __init__(
        self,
        agent: AgentDef,
        frame_dir,
        scale: float,
        sounds: SoundPlayer,
        idle_seconds: float = 12.0,
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.agent_def = agent
        self.frame_dir = frame_dir
        self.scale = scale
        self.sounds = sounds
        self.idle_seconds = idle_seconds
        self.animator = Animator(agent, on_sound=self._sound)
        self.pixbuf: GdkPixbuf.Pixbuf | None = None
        self._cache: dict[tuple, GdkPixbuf.Pixbuf] = {}
        self._timer = 0
        self._idle_timer = 0
        self._press: tuple[float, float] | None = None
        self._origin: tuple[int, int] = (0, 0)
        self._dragging = False
        self._hidden_for_shot = False
        self._was_visible = True
        self._dodge_enabled = False
        self._dodge_hold_key = "Shift"
        self._dodge_timer = 0
        self._skitter_timer = 0
        self._skitter_path: list[tuple[int, int]] = []
        self.on_click: Callable[[], None] | None = None
        self.on_menu: Callable[[Gtk.Menu], None] | None = None
        self.on_moved: Callable[[], None] | None = None
        self.chat_is_open: Callable[[], bool] | None = None

        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.stick()
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.BUTTON1_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self._draw)
        self.add(self.area)
        self.connect("realize", self._realized)
        self.connect("button-press-event", self._pressed)
        self.connect("button-release-event", self._released)
        self.connect("motion-notify-event", self._moved)
        self.connect("configure-event", self._configured)
        self.connect("destroy", lambda *_: self._clear_timers())

        self._apply_size()
        self._show_frame()
        self._arm_frame()
        self._arm_idle()

    def display_size(self) -> tuple[int, int]:
        fw, fh = self.agent_def.frame_size
        target_w = max(48, int(124 * self.scale))
        target_h = max(36, int(round(fh * target_w / max(fw, 1))))
        return target_w, target_h

    def reload(self, agent: AgentDef, frame_dir) -> None:
        self.agent_def = agent
        self.frame_dir = frame_dir
        self.animator = Animator(agent, on_sound=self._sound)
        self._cache.clear()
        self._apply_size()
        self._show_frame()
        self._arm_frame()

    def _apply_size(self) -> None:
        width, height = self.display_size()
        self.set_size_request(width, height)
        self.resize(width, height)

    def set_scale(self, scale: float) -> None:
        self.scale = scale
        self._cache.clear()
        self._apply_size()
        self._show_frame()

    def set_dodge(self, enabled: bool, hold_key: str = "Shift") -> None:
        self._dodge_hold_key = normalize_hold_key(hold_key)
        self._dodge_enabled = bool(enabled)
        if self._dodge_enabled:
            self._arm_dodge()
        else:
            self._clear_dodge()

    def place_default(self) -> None:
        display = self.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        work = monitor.get_workarea()
        width, height = self.display_size()
        self.move(work.x + work.width - width - 28, work.y + work.height - height - 36)

    def play(self, name: str, interrupt: bool = False) -> None:
        self.animator.play(name, interrupt=interrupt)
        if interrupt:
            self._show_frame()
            self._arm_frame()

    def play_mood(self, mood: str, interrupt: bool = False) -> str:
        name = self.animator.play_mood(mood, interrupt=interrupt)
        if interrupt:
            self._show_frame()
            self._arm_frame()
        return name

    def hide_for_capture(self) -> None:
        self._was_visible = self.get_visible()
        self._hidden_for_shot = True
        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

    def restore_after_capture(self) -> None:
        if self._hidden_for_shot and self._was_visible:
            self.show_all()
        self._hidden_for_shot = False

    def _sound(self, sound_id: str) -> None:
        self.sounds.play(sound_id)

    def _show_frame(self) -> None:
        view = self.animator.current_view()
        key = (view.animation, view.index, tuple(tuple(cell) for cell in view.images), self.display_size())
        pixbuf = self._cache.get(key)
        if pixbuf is None:
            image = compose_frame(self.frame_dir, view.images, self.agent_def.frame_size, hd=True)
            target = self.display_size()
            if image.size != target:
                image = image.resize(target, Image.Resampling.LANCZOS)
            pixbuf = _pixbuf(image)
            self._cache[key] = pixbuf
            if len(self._cache) > 240:
                self._cache.pop(next(iter(self._cache)))
        self.pixbuf = pixbuf
        if view.sound:
            self._sound(view.sound)
        self.area.queue_draw()

    def _draw(self, _area, ctx) -> bool:
        import cairo

        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        if self.pixbuf is not None:
            Gdk.cairo_set_source_pixbuf(ctx, self.pixbuf, 0, 0)
            ctx.paint()
        return True

    def _arm_frame(self) -> None:
        if self._timer:
            GLib.source_remove(self._timer)
        delay = self.animator.current_view().duration_ms
        self._timer = GLib.timeout_add(delay, self._tick)

    def _tick(self) -> bool:
        self.animator.advance()
        self._show_frame()
        self._arm_frame()
        return False

    def _arm_idle(self) -> None:
        if self._idle_timer:
            GLib.source_remove(self._idle_timer)
        delay = int((self.idle_seconds + random.random() * self.idle_seconds) * 1000)
        self._idle_timer = GLib.timeout_add(delay, self._idle)

    def _idle(self) -> bool:
        if self.animator.current in ("RestPose",) and not self.animator.queue:
            self.animator.idle()
        self._arm_idle()
        return False

    def _clear_timers(self) -> None:
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        if self._idle_timer:
            GLib.source_remove(self._idle_timer)
            self._idle_timer = 0
        self._clear_dodge()

    def _clear_dodge(self) -> None:
        if self._dodge_timer:
            GLib.source_remove(self._dodge_timer)
            self._dodge_timer = 0
        if self._skitter_timer:
            GLib.source_remove(self._skitter_timer)
            self._skitter_timer = 0
        self._skitter_path = []

    def _arm_dodge(self) -> None:
        if self._dodge_timer:
            return
        self._dodge_timer = GLib.timeout_add(40, self._dodge_poll)

    def _workarea(self) -> tuple[int, int, int, int]:
        display = self.get_display()
        window = self.get_window()
        monitor = display.get_monitor_at_window(window) if window else (display.get_primary_monitor() or display.get_monitor(0))
        work = monitor.get_workarea()
        return int(work.x), int(work.y), int(work.width), int(work.height)

    def _pointer_state(self) -> tuple[int, int, int] | None:
        display = self.get_display()
        if display is None:
            return None
        try:
            device = display.get_default_seat().get_pointer()
            _screen, mx, my = device.get_position()
            keymap = Gdk.Keymap.get_for_display(display)
            return int(mx), int(my), int(keymap.get_modifier_state())
        except Exception:
            return None

    def _dodge_poll(self) -> bool:
        if not self._dodge_enabled:
            self._dodge_timer = 0
            return False
        if self.chat_is_open and self.chat_is_open():
            if self._skitter_path:
                self._skitter_path = []
            return True
        if self._skitter_path or self._dragging or not self.get_visible() or self._hidden_for_shot:
            return True
        state = self._pointer_state()
        if state is None:
            return True
        mx, my, modifiers = state
        if hold_is_down(self._dodge_hold_key, modifiers):
            return True
        x, y = self.get_position()
        w, h = self.display_size()
        if not pointer_hits(mx, my, x, y, w, h):
            return True
        nx, ny = flee_position(mx, my, x, y, w, h, self._workarea())
        if abs(nx - x) + abs(ny - y) < 8:
            return True
        self._start_skitter(x, y, nx, ny)
        return True

    def _start_skitter(self, x: int, y: int, nx: int, ny: int) -> None:
        self._skitter_path = skitter_steps(x, y, nx, ny, work=self._workarea(), size=self.display_size())
        if self.animator.has("Scurry"):
            self.play("Scurry", interrupt=True)
        else:
            self.play_mood("dodge", interrupt=True)
        if self._skitter_timer:
            GLib.source_remove(self._skitter_timer)
        self._skitter_timer = GLib.timeout_add(18, self._skitter_tick)

    def _skitter_tick(self) -> bool:
        if not self._skitter_path:
            self._skitter_timer = 0
            if self.on_moved:
                self.on_moved()
            return False
        self.move(*self._skitter_path.pop(0))
        if self.on_moved:
            self.on_moved()
        return True

    def _set_cursor(self, name: str) -> None:
        window = self.get_window()
        if window is None:
            return
        window.set_cursor(Gdk.Cursor.new_from_name(self.get_display(), name))

    def _realized(self, *_args) -> None:
        self._set_cursor("grab")

    def _pressed(self, _win, event) -> bool:
        if event.button == 3:
            menu = Gtk.Menu()
            if self.on_menu:
                self.on_menu(menu)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        if event.button == 1:
            self._press = (event.x_root, event.y_root)
            self._origin = self.get_position()
            self._dragging = False
            self._set_cursor("grabbing")
        return True

    def _moved(self, _win, event) -> bool:
        if self._press is None:
            return False
        dx = event.x_root - self._press[0]
        dy = event.y_root - self._press[1]
        if abs(dx) + abs(dy) > 4:
            self._dragging = True
            self.move(int(self._origin[0] + dx), int(self._origin[1] + dy))
            if self.on_moved:
                self.on_moved()
        return True

    def _configured(self, _win, _event) -> bool:
        if self.on_moved and self._dragging:
            self.on_moved()
        return False

    def _released(self, _win, event) -> bool:
        if event.button == 1:
            dragged = self._dragging
            self._press = None
            self._dragging = False
            if dragged:
                if self.on_moved:
                    self.on_moved()
            elif self.on_click:
                self.on_click()
            self._set_cursor("grab")
        return True
