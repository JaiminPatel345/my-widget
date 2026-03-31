"""Right panel: App launcher only."""

import subprocess
import threading
import cairo
from gi.repository import Gtk, Gdk, GLib

from widgets.config import CFG, PINK, WHITE, GREY, DIM
from widgets.helpers import rr, sc, load_icon, blit_icon, color_initial_icon
from widgets.icons import draw_icon


class RightPanel(Gtk.DrawingArea):
    PW, PH = 220, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._apps = CFG["apps"]
        self._hover = -1
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._on_click)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event", self._on_leave)
        threading.Thread(target=self._preload, daemon=True).start()

    def _preload(self):
        for a in self._apps:
            load_icon(a["icon"], 48, a.get("icon_path"))
        GLib.idle_add(self.queue_draw)

    PAD = 10

    def _app_rect(self, i):
        bw = self.PW - self.PAD * 2
        bh = 46
        return self.PAD, 18 + i * (bh + 6), bw, bh

    def _on_click(self, w, event):
        for i, app in enumerate(self._apps):
            x, y, bw, bh = self._app_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                try:
                    subprocess.Popen(app["cmd"].split())
                except Exception as e:
                    print(f"Launch error: {e}")
                return

    def _on_motion(self, w, event):
        h = -1
        for i in range(len(self._apps)):
            x, y, bw, bh = self._app_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                h = i; break
        if h != self._hover:
            self._hover = h; self.queue_draw()

    def _on_leave(self, *_):
        self._hover = -1; self.queue_draw()

    def _draw(self, widget, cr):
        pad = self.PAD

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9); sc(cr, DIM)
        cr.move_to(pad, 13); cr.show_text("LAUNCH")

        for i, app in enumerate(self._apps):
            x, y, bw, bh = self._app_rect(i)
            is_h = (i == self._hover)
            ac = tuple(app["color"])

            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*ac[:3], 0.18 if is_h else 0.04); cr.fill()
            if is_h:
                rr(cr, x, y, bw, bh, 10)
                cr.set_source_rgba(*ac[:3], 0.55)
                cr.set_line_width(1); cr.stroke()

            isurf = load_icon(app["icon"], 48, app.get("icon_path"))
            if isurf:
                blit_icon(cr, isurf, x + 26, y + bh / 2, 30)
            else:
                color_initial_icon(cr, x + 26, y + bh / 2, 14, app["name"][0], ac)

            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(13)
            sc(cr, WHITE if is_h else GREY)
            cr.move_to(x + 50, y + bh / 2 + 5); cr.show_text(app["name"])

            if is_h:
                cr.set_font_size(14); sc(cr, ac)
                cr.move_to(x + bw - 14, y + bh / 2 + 5); cr.show_text(">")
