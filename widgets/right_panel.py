"""Right panel: App launcher + Action buttons (large icon cards)."""

import subprocess
import threading
import cairo
from gi.repository import Gtk, Gdk, GLib

from widgets.config import CFG, PINK, CYAN, WHITE, GREY, DIM, BORDER, RED, GREEN, ORANGE
from widgets.helpers import rr, draw_card, sc, load_icon, blit_icon, color_initial_icon
from widgets.icons import draw_icon

# Height per app row
_APP_H = 46
_APP_GAP = 5
_APP_TOP = 18

# Action card size
_ACT_H = 75
_ACT_GAP = 8


class RightPanel(Gtk.DrawingArea):
    PW, PH = 220, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._apps = CFG["apps"]
        self._actions = CFG["system_actions"]
        self._hover_app = -1
        self._hover_act = -1
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
        return self.PAD, _APP_TOP + i * (_APP_H + _APP_GAP), bw, _APP_H

    def _act_rect(self, i):
        """2-column grid below apps."""
        apps_bot = _APP_TOP + len(self._apps) * (_APP_H + _APP_GAP) + 14
        bw = (self.PW - self.PAD * 2 - _ACT_GAP) // 2
        col = i % 2
        row = i // 2
        x = self.PAD + col * (bw + _ACT_GAP)
        y = apps_bot + 16 + row * (_ACT_H + _ACT_GAP)
        return x, y, bw, _ACT_H

    def _on_click(self, w, event):
        for i, app in enumerate(self._apps):
            x, y, bw, bh = self._app_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                try: subprocess.Popen(app["cmd"].split())
                except Exception as e: print(f"Launch error: {e}")
                return
        for i, act in enumerate(self._actions):
            x, y, bw, bh = self._act_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                if act.get("confirm"):
                    d = Gtk.MessageDialog(
                        message_type=Gtk.MessageType.WARNING,
                        buttons=Gtk.ButtonsType.OK_CANCEL,
                        text=f"{act['label']}?")
                    r = d.run(); d.destroy()
                    if r != Gtk.ResponseType.OK: return
                cmd = act["cmd"]
                def _run(c=cmd):
                    try:
                        subprocess.run(c, stderr=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL)
                    except Exception as e:
                        print(f"Sys error: {e}")
                threading.Thread(target=_run, daemon=True).start()
                return

    def _on_motion(self, w, event):
        ha, hac = -1, -1
        for i in range(len(self._apps)):
            x, y, bw, bh = self._app_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                ha = i; break
        for i in range(len(self._actions)):
            x, y, bw, bh = self._act_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                hac = i; break
        if ha != self._hover_app or hac != self._hover_act:
            self._hover_app = ha; self._hover_act = hac; self.queue_draw()

    def _on_leave(self, *_):
        self._hover_app = self._hover_act = -1; self.queue_draw()

    def _draw(self, widget, cr):
        pad = self.PAD

        # ── App rows ──
        for i, app in enumerate(self._apps):
            x, y, bw, bh = self._app_rect(i)
            is_h = (i == self._hover_app)
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
            cr.set_font_size(13); sc(cr, WHITE if is_h else GREY)
            cr.move_to(x + 50, y + bh / 2 + 5); cr.show_text(app["name"])
            if is_h:
                cr.set_font_size(14); sc(cr, ac)
                cr.move_to(x + bw - 14, y + bh / 2 + 5); cr.show_text(">")

        # Divider
        sep_y = _APP_TOP + len(self._apps) * (_APP_H + _APP_GAP) + 2
        sc(cr, BORDER); cr.set_line_width(1)
        cr.move_to(pad, sep_y); cr.line_to(self.PW - pad, sep_y); cr.stroke()

        # ── Action cards (large icon style) ──
        for i, act in enumerate(self._actions):
            x, y, bw, bh = self._act_rect(i)
            is_h = (i == self._hover_act)
            bc = tuple(act.get("color", GREY))

            # Card background
            rr(cr, x, y, bw, bh, 12)
            cr.set_source_rgba(*bc[:3], 0.18 if is_h else 0.08); cr.fill()
            if is_h:
                rr(cr, x, y, bw, bh, 12)
                sc(cr, bc); cr.set_line_width(1.5); cr.stroke()

            # Large centered icon
            icon_color = bc if is_h else tuple(list(bc[:3]) + [0.7])
            draw_icon(cr, act["icon"], x + bw / 2, y + bh / 2 - 8, 34, icon_color)

            # Label below icon
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(10)
            sc(cr, bc if is_h else GREY)
            te = cr.text_extents(act["label"])
            cr.move_to(x + bw / 2 - te.width / 2, y + bh - 8)
            cr.show_text(act["label"])
