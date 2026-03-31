"""Files panel: Quick-link directory column."""

import os
import subprocess
import cairo
from gi.repository import Gtk, Gdk, GLib

from widgets.config import CFG, CARD, CARD2, PINK, CYAN, WHITE, GREY, DIM, BORDER, ORANGE, GREEN
from widgets.helpers import rr, draw_card, sc
from widgets.icons import draw_icon

# Color per icon type
_FILE_COLORS = {
    "home": PINK,
    "folder": GREY,
    "downloads": CYAN,
}


class FilesPanel(Gtk.DrawingArea):
    PW, PH = 160, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._files = CFG["files"]
        self._hover = -1
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._on_click)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event", self._on_leave)

    PAD = 10

    def _entry_rect(self, i):
        bw = self.PW - self.PAD * 2
        bh = 46
        return self.PAD, 18 + i * (bh + 6), bw, bh

    def _on_click(self, w, event):
        for i, f in enumerate(self._files):
            x, y, bw, bh = self._entry_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                path = f["path"]
                try:
                    subprocess.Popen(["xdg-open", path])
                except Exception as e:
                    print(f"Open error: {e}")
                return

    def _on_motion(self, w, event):
        h = -1
        for i in range(len(self._files)):
            x, y, bw, bh = self._entry_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                h = i
                break
        if h != self._hover:
            self._hover = h
            self.queue_draw()

    def _on_leave(self, *_):
        if self._hover != -1:
            self._hover = -1
            self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad = self.PAD

        for i, f in enumerate(self._files):
            x, y, bw, bh = self._entry_rect(i)
            is_h = (i == self._hover)
            icon_name = f.get("icon", "folder")
            ic = _FILE_COLORS.get(icon_name, GREY)

            # Background
            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*ic[:3], 0.15 if is_h else 0.04)
            cr.fill()
            if is_h:
                rr(cr, x, y, bw, bh, 10)
                cr.set_source_rgba(*ic[:3], 0.5)
                cr.set_line_width(1)
                cr.stroke()

            # Icon
            draw_icon(cr, icon_name, x + 22, y + bh / 2, 20, ic)

            # Label
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(12)
            sc(cr, WHITE if is_h else GREY)
            cr.move_to(x + 40, y + bh / 2 + 4)
            cr.show_text(f["label"])
