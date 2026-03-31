"""Left panel: Profile, Weather, Toggles."""

import math
import os
import subprocess
import threading
import cairo
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from widgets.config import (CFG, CARD, CARD2, PINK, CYAN, WHITE, GREY, DIM,
                            BORDER, PURPLE)
from widgets.helpers import rr, draw_card, sc, _pb_to_surface
from widgets.icons import draw_icon

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class LeftPanel(Gtk.DrawingArea):
    PW, PH = 300, 560

    _TOG_CARD_Y = 355
    _TOG_CELL_H = 52
    _TOG_CELL_GAP = 8

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._weather = "Fetching..."
        self._temp = "--C"
        self._condition = ""
        self._wcode = 116
        self._toggles = CFG["system_toggles"]
        self._tog_states = [False] * len(self._toggles)
        self._hover = -1
        self._profile = self._load_profile()
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._on_click)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event", self._on_leave)
        GLib.timeout_add(2000, lambda: (self.queue_draw(), True)[1])
        threading.Thread(target=self._fetch_weather, daemon=True).start()
        threading.Thread(target=self._detect_states, daemon=True).start()

    def _load_profile(self):
        for p in [CFG["profile_image"],
                  os.path.expanduser("~/Pictures/profile.png"),
                  os.path.expanduser("~/Pictures/avatar.jpg")]:
            if os.path.exists(p):
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, 130, 130, True)
                    return _pb_to_surface(pb)
                except Exception:
                    pass
        return None

    def _fetch_weather(self):
        if not HAS_REQUESTS:
            self._temp = "--C"; self._condition = "install requests"
            GLib.idle_add(self.queue_draw); return
        try:
            data = requests.get(
                f"https://wttr.in/{CFG['city']}?format=j1", timeout=6).json()
            cur = data["current_condition"][0]
            self._temp = cur["temp_C"] + "C"
            self._condition = cur["weatherDesc"][0]["value"]
            self._wcode = int(cur["weatherCode"])
        except Exception:
            self._temp = "--C"; self._condition = "Unavailable"
        GLib.idle_add(self.queue_draw)

    def _detect_states(self):
        try:
            out = subprocess.check_output(
                ["nmcli", "radio", "wifi"], stderr=subprocess.DEVNULL).decode().strip()
            self._tog_states[0] = (out == "enabled")
        except Exception: pass
        try:
            out = subprocess.check_output(
                ["bluetoothctl", "show"], stderr=subprocess.DEVNULL).decode()
            self._tog_states[1] = "Powered: yes" in out
        except Exception: pass
        GLib.idle_add(self.queue_draw)

    def _tog_rect(self, i):
        pad = 12
        cw = self.PW - pad * 2
        bw = (cw - self._TOG_CELL_GAP) // 2
        col = i % 2
        row = i // 2
        x = pad + col * (bw + self._TOG_CELL_GAP)
        y = self._TOG_CARD_Y + 10 + row * (self._TOG_CELL_H + self._TOG_CELL_GAP)
        return x, y, bw, self._TOG_CELL_H

    def _on_click(self, w, event):
        for i, tog in enumerate(self._toggles):
            x, y, bw, bh = self._tog_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                self._tog_states[i] = not self._tog_states[i]
                on = self._tog_states[i]
                cmd = tog["cmd_on"] if on else tog["cmd_off"]
                subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
                self.queue_draw(); return

    def _on_motion(self, w, event):
        h = -1
        for i in range(len(self._toggles)):
            x, y, bw, bh = self._tog_rect(i)
            if x <= event.x <= x + bw and y <= event.y <= y + bh:
                h = i; break
        if h != self._hover:
            self._hover = h; self.queue_draw()

    def _on_leave(self, *_):
        if self._hover != -1:
            self._hover = -1; self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad = 12

        # ── Profile ──
        img_cx, img_cy, img_r = w // 2, 95, 56
        cr.save()
        cr.arc(img_cx, img_cy, img_r, 0, 2 * math.pi)
        cr.clip()
        if self._profile:
            sw, sh = self._profile.get_width(), self._profile.get_height()
            sc_ = (img_r * 2) / min(sw, sh)
            cr.translate(img_cx - sw * sc_ / 2, img_cy - sh * sc_ / 2)
            cr.scale(sc_, sc_)
            cr.set_source_surface(self._profile, 0, 0)
        else:
            g = cairo.RadialGradient(img_cx, img_cy - 20, 0, img_cx, img_cy, img_r)
            g.add_color_stop_rgba(0, *PINK[:3], 1)
            g.add_color_stop_rgba(1, *PURPLE[:3], 1)
            cr.set_source(g)
        cr.paint()
        cr.restore()

        cr.arc(img_cx, img_cy, img_r + 2.5, 0, 2 * math.pi)
        sc(cr, PINK); cr.set_line_width(2.5); cr.stroke()

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(20); sc(cr, PINK)
        ne = cr.text_extents(CFG["display_name"])
        cr.move_to(w / 2 - ne.width / 2, 183); cr.show_text(CFG["display_name"])

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, GREY)
        sub = CFG["subtitle"]
        se = cr.text_extents(sub)
        cr.move_to(w / 2 - se.width / 2, 200); cr.show_text(sub)

        sc(cr, BORDER); cr.set_line_width(1)
        cr.move_to(pad, 212); cr.line_to(w - pad, 212); cr.stroke()

        # ── Weather ──
        draw_card(cr, pad, 220, w - pad * 2, 120, 12, CARD2)
        self._draw_weather_icon(cr, pad + 50, 275, 36)

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(32); sc(cr, WHITE)
        cr.move_to(pad + 90, 272); cr.show_text(self._temp)
        deg_x = pad + 90 + cr.text_extents(self._temp).width + 2
        cr.set_font_size(14); cr.move_to(deg_x, 252); cr.show_text("o")

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, PINK)
        cr.move_to(pad + 90, 292); cr.show_text(self._condition[:22])

        msgs = {"Clear": "Perfect day outside!", "Sunny": "Go for a walk!",
                "Cloud": "Maybe bring a jacket.", "Rain": "Grab your umbrella!",
                "Snow": "Stay warm and cozy!"}
        msg = next((v for k, v in msgs.items()
                    if k.lower() in self._condition.lower()), "Have a great day!")
        cr.set_font_size(10); sc(cr, GREY)
        me = cr.text_extents(msg)
        cr.move_to(w / 2 - me.width / 2, 330); cr.show_text(msg)

        # ── Toggles ──
        n_rows = math.ceil(len(self._toggles) / 2)
        card_h = 10 + n_rows * (self._TOG_CELL_H + self._TOG_CELL_GAP) - self._TOG_CELL_GAP + 10
        draw_card(cr, pad, self._TOG_CARD_Y, w - pad * 2, card_h, 12, CARD2)

        for i, tog in enumerate(self._toggles):
            x, y, bw, bh = self._tog_rect(i)
            is_on = self._tog_states[i]
            is_h = (self._hover == i)
            icon_name = tog["icon"]
            if icon_name == "speaker" and is_on:
                icon_name = "speaker_muted"
            ic = PINK if is_on else (GREY if is_h else DIM)

            # Cell background
            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*PINK[:3], 0.22 if is_on else (0.10 if is_h else 0.05))
            cr.fill()
            if is_on or is_h:
                rr(cr, x, y, bw, bh, 10)
                sc(cr, PINK if is_on else GREY)
                cr.set_line_width(1.5); cr.stroke()

            # Large icon
            draw_icon(cr, icon_name, x + 28, y + bh / 2, 22, ic)

            # Label
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(13); sc(cr, WHITE if is_on else ic)
            cr.move_to(x + 46, y + bh / 2 + 5); cr.show_text(tog["label"])

    def _draw_weather_icon(self, cr, cx, cy, size):
        code = self._wcode
        if code == 113:
            sc(cr, (1.0, 0.85, 0.3, 1.0))
            cr.arc(cx, cy, size * 0.35, 0, 2 * math.pi); cr.fill()
            cr.set_line_width(2.5)
            for i in range(8):
                a = i * math.pi / 4
                cr.move_to(cx + size*0.5*math.cos(a), cy + size*0.5*math.sin(a))
                cr.line_to(cx + size*0.7*math.cos(a), cy + size*0.7*math.sin(a))
                cr.stroke()
        elif code in (116, 119, 122):
            sc(cr, GREY)
            cr.arc(cx-size*0.15, cy, size*0.35, 0, 2*math.pi); cr.fill()
            cr.arc(cx+size*0.2, cy-size*0.05, size*0.28, 0, 2*math.pi); cr.fill()
            cr.arc(cx+size*0.1, cy+size*0.15, size*0.25, 0, 2*math.pi); cr.fill()
            cr.rectangle(cx-size*0.35, cy, size*0.7, size*0.3); cr.fill()
        elif code in (176, 263, 293, 296, 299, 302, 356):
            sc(cr, GREY)
            cr.arc(cx-size*0.1, cy-size*0.15, size*0.3, 0, 2*math.pi); cr.fill()
            cr.arc(cx+size*0.2, cy-size*0.1, size*0.22, 0, 2*math.pi); cr.fill()
            cr.rectangle(cx-size*0.3, cy-size*0.05, size*0.6, size*0.2); cr.fill()
            sc(cr, CYAN); cr.set_line_width(2)
            for dx in [-0.15, 0.05, 0.25]:
                cr.move_to(cx+size*dx, cy+size*0.25)
                cr.line_to(cx+size*dx-size*0.08, cy+size*0.5); cr.stroke()
        elif code in (200, 389):
            sc(cr, GREY)
            cr.arc(cx, cy-size*0.2, size*0.3, 0, 2*math.pi); cr.fill()
            sc(cr, (1.0, 0.85, 0.3, 1.0)); cr.set_line_width(2.5)
            cr.move_to(cx+size*0.05, cy+size*0.05)
            cr.line_to(cx-size*0.1, cy+size*0.35)
            cr.line_to(cx+size*0.05, cy+size*0.35)
            cr.line_to(cx-size*0.05, cy+size*0.6); cr.stroke()
        elif code in (227, 230):
            sc(cr, WHITE)
            for i in range(6):
                a = i * math.pi / 3
                cr.move_to(cx, cy)
                cr.line_to(cx+size*0.5*math.cos(a), cy+size*0.5*math.sin(a))
            cr.set_line_width(2); cr.stroke()
        else:
            draw_icon(cr, "moon", cx, cy, size * 1.4, PINK)
