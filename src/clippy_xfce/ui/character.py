"""Always-on-top animated Clippy overlay."""

from __future__ import annotations

import io
import random
from collections.abc import Callable

import clippy_xfce.gi_setup  # noqa: F401
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from clippy_xfce.animator import Animator
from clippy_xfce.sounds import SoundPlayer
from clippy_xfce.sprites import AgentDef, compose_frame


def _pixbuf(image) -> GdkPixbuf.Pixbuf:
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
        self._timer = 0
        self._idle_timer = 0
        self._press: tuple[float, float] | None = None
        self._hidden_for_shot = False
        self._was_visible = True
        self.on_click: Callable[[], None] | None = None
        self.on_menu: Callable[[Gtk.Menu], None] | None = None
        self.on_moved: Callable[[], None] | None = None

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
            | Gdk.EventMask.BUTTON_MOTION_MASK
        )

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self._draw)
        self.add(self.area)
        self.connect("button-press-event", self._pressed)
        self.connect("button-release-event", self._released)
        self.connect("motion-notify-event", self._moved)
        self.connect("destroy", lambda *_: self._clear_timers())

        fw, fh = agent.frame_size
        self.set_default_size(int(fw * scale), int(fh * scale))
        self._show_frame()
        self._arm_frame()
        self._arm_idle()

    def place_default(self) -> None:
        display = self.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        work = monitor.get_workarea()
        fw, fh = self.agent_def.frame_size
        width, height = int(fw * self.scale), int(fh * self.scale)
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
        image = compose_frame(self.frame_dir, view.images, self.agent_def.frame_size)
        pixbuf = _pixbuf(image)
        fw, fh = self.agent_def.frame_size
        self.pixbuf = pixbuf.scale_simple(
            int(fw * self.scale),
            int(fh * self.scale),
            GdkPixbuf.InterpType.BILINEAR,
        )
        if view.sound:
            self._sound(view.sound)
        self.area.queue_draw()
        self._update_shape()

    def _update_shape(self) -> None:
        window = self.get_window()
        if window is None or self.pixbuf is None:
            return
        import cairo

        width, height = self.pixbuf.get_width(), self.pixbuf.get_height()
        surface = cairo.ImageSurface(cairo.FORMAT_A8, width, height)
        ctx = cairo.Context(surface)
        Gdk.cairo_set_source_pixbuf(ctx, self.pixbuf, 0, 0)
        ctx.paint()
        region = Gdk.cairo_region_create_from_surface(surface)
        window.input_shape_combine_region(region, 0, 0)

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
        return False

    def _moved(self, _win, event) -> bool:
        if self._press and event.state & Gdk.ModifierType.BUTTON1_MASK:
            dx = abs(event.x_root - self._press[0])
            dy = abs(event.y_root - self._press[1])
            if dx + dy > 6:
                self.begin_move_drag(1, int(event.x_root), int(event.y_root), event.time)
                self._press = None
                if self.on_moved:
                    GLib.timeout_add(80, lambda: (self.on_moved() or False))
        return False

    def _released(self, _win, event) -> bool:
        if event.button == 1 and self._press is not None:
            if self.on_click:
                self.on_click()
        self._press = None
        if self.on_moved:
            self.on_moved()
        return False
