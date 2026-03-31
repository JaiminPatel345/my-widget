#!/usr/bin/env python3
"""
Desktop Widget - Glassmorphism Panel
Sections: Profile + Weather | Clock | Calendar | Music | App Launcher | Quick Toggles
Always-on-desktop, center screen, no titlebar, transparent background
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango, PangoCairo
import cairo
import datetime
import subprocess
import os
import math
import threading
import calendar as cal_mod

# ─── CONFIG ───────────────────────────────────────────────────────────────────
USER_NAME   = "Jaimin Detroja"           # ← Change this
PROFILE_IMG = os.path.expanduser("~/.config/desktop-widget/profile.jpg")
CITY        = "Vadodara"            # ← Your city for weather
WIDGET_W    = 650
WIDGET_H    = 630

APPS = [
    {"name": "Chrome",   "icon": "🌐", "cmd": "google-chrome"},
    {"name": "Discord",  "icon": "💬", "cmd": "discord"},
    {"name": "Brave",    "icon": "🦁", "cmd": "brave-browser"},
    {"name": "YouTube",  "icon": "▶",  "cmd": "xdg-open https://youtube.com"},
    {"name": "Calc",     "icon": "🧮", "cmd": "gnome-calculator"},
]

# ─── COLORS ──────────────────────────────────────────────────────────────────
def rgba(r, g, b, a=1.0): return (r/255, g/255, b/255, a)

C_BG         = rgba(12, 10, 35, 0.88)
C_CARD       = rgba(255, 255, 255, 0.07)
C_BORDER     = rgba(255, 255, 255, 0.14)
C_WHITE      = (1.0, 1.0, 1.0, 1.0)
C_DIM        = (1.0, 1.0, 1.0, 0.50)
C_FAINT      = (1.0, 1.0, 1.0, 0.22)
C_PURPLE     = rgba(161, 141, 250, 1.0)
C_BLUE       = rgba(100, 126, 234, 1.0)
C_ACTIVE_BG  = rgba(161, 141, 250, 0.28)


def set_rgba(cr, c):
    cr.set_source_rgba(*c)


def rounded_rect(cr, x, y, w, h, r=14):
    cr.new_sub_path()
    cr.arc(x+r,     y+r,     r, math.pi,      1.5*math.pi)
    cr.arc(x+w-r,   y+r,     r, 1.5*math.pi,  0)
    cr.arc(x+w-r,   y+h-r,   r, 0,             0.5*math.pi)
    cr.arc(x+r,     y+h-r,   r, 0.5*math.pi,  math.pi)
    cr.close_path()


def glass_card(cr, x, y, w, h, r=16):
    rounded_rect(cr, x, y, w, h, r)
    set_rgba(cr, C_CARD)
    cr.fill()
    rounded_rect(cr, x, y, w, h, r)
    set_rgba(cr, C_BORDER)
    cr.set_line_width(1.0)
    cr.stroke()
    # top highlight
    cr.save()
    rounded_rect(cr, x, y, w, h, r)
    cr.clip()
    shine = cairo.LinearGradient(x, y, x, y+36)
    shine.add_color_stop_rgba(0, 1, 1, 1, 0.10)
    shine.add_color_stop_rgba(1, 1, 1, 1, 0.00)
    cr.set_source(shine)
    cr.rectangle(x, y, w, 36)
    cr.fill()
    cr.restore()


# ─── UTILITIES ───────────────────────────────────────────────────────────────

def run_cmd(cmd, timeout=3):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def launch(cmd):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ─── WEATHER ─────────────────────────────────────────────────────────────────

class Weather:
    def __init__(self):
        self.temp = "—"
        self.desc = "Fetching…"
        self.icon = "🌤"
        self._do_fetch()

    def _do_fetch(self):
        def fetch():
            try:
                import urllib.request
                url = f"https://wttr.in/{CITY}?format=%t+%C"
                with urllib.request.urlopen(url, timeout=6) as resp:
                    data = resp.read().decode().strip()
                parts = data.split(" ", 1)
                self.temp = parts[0].replace("+", "").strip()
                raw_desc = parts[1].strip() if len(parts) > 1 else ""
                self.desc = raw_desc[:18]
                d = raw_desc.lower()
                if "sun" in d or "clear" in d: self.icon = "☀"
                elif "cloud" in d:              self.icon = "⛅"
                elif "rain" in d:               self.icon = "🌧"
                elif "snow" in d:               self.icon = "❄"
                elif "thunder" in d:            self.icon = "⛈"
                elif "fog" in d or "mist" in d: self.icon = "🌫"
                else:                           self.icon = "🌤"
            except Exception:
                self.temp = "N/A"
                self.desc = "No network"
                self.icon = "☁"
        threading.Thread(target=fetch, daemon=True).start()
        GLib.timeout_add_seconds(600, self._do_fetch)


# ─── STATE ───────────────────────────────────────────────────────────────────

class State:
    def __init__(self):
        self.cd_angle   = 0.0
        self.cd_playing = False
        self.wifi       = "enabled" in run_cmd("nmcli radio wifi").lower()
        self.bt         = "yes"     in run_cmd("bluetoothctl show | grep Powered").lower()
        self.night      = False
        self.bright     = True


# ─── MAIN WINDOW ─────────────────────────────────────────────────────────────

class Widget(Gtk.Window):

    def __init__(self):
        super().__init__()
        self.weather  = Weather()
        self.state    = State()
        self._hits    = {}           # name → (x,y,w,h,callback)
        self._profile = self._load_profile()

        # window flags
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.set_accept_focus(False)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_default_size(WIDGET_W, WIDGET_H)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        sw, sh = screen.get_width(), screen.get_height()
        self.move((sw - WIDGET_W) // 2, (sh - WIDGET_H) // 2)

        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._on_click)
        self.connect("draw",               self._draw)
        self.show_all()

        GLib.timeout_add(1000, self._tick)
        GLib.timeout_add(50,   self._tick_cd)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _load_profile(self):
        if os.path.exists(PROFILE_IMG):
            try:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(PROFILE_IMG, 70, 70, True)
            except Exception:
                pass
        return None

    def _tick(self):
        self.queue_draw()
        return True

    def _tick_cd(self):
        if self.state.cd_playing:
            self.state.cd_angle = (self.state.cd_angle + 1.8) % 360
        self.queue_draw()
        return True

    def _on_click(self, _w, event):
        x, y = event.x, event.y
        for rx, ry, rw, rh, cb in self._hits.values():
            if rx <= x <= rx+rw and ry <= y <= ry+rh:
                cb()
                self.queue_draw()
                return

    def _reg(self, name, x, y, w, h, cb):
        self._hits[name] = (x, y, w, h, cb)

    # ── text renderer ────────────────────────────────────────────────────────

    def _txt(self, cr, text, x, y, size=11, bold=False,
             color=None, center=False):
        if color is None: color = C_WHITE
        layout = self.create_pango_layout(text)
        fd = Pango.FontDescription.from_string(
            f"{'Ubuntu Bold' if bold else 'Ubuntu'} {size}")
        layout.set_font_description(fd)
        lw, lh = layout.get_pixel_size()
        ox = x - lw//2 if center else x
        cr.save()
        cr.move_to(ox, y - lh//2)
        cr.set_source_rgba(*color)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

    def _txt_grad(self, cr, text, x, y, size=36, bold=True, center=False):
        layout = self.create_pango_layout(text)
        fd = Pango.FontDescription.from_string(
            f"{'Ubuntu Bold' if bold else 'Ubuntu'} {size}")
        layout.set_font_description(fd)
        lw, lh = layout.get_pixel_size()
        ox = x - lw//2 if center else x
        cr.save()
        g = cairo.LinearGradient(ox, y - lh//2, ox + lw, y + lh//2)
        g.add_color_stop_rgba(0, 1, 1, 1, 1)
        g.add_color_stop_rgba(1, *C_PURPLE[:3], 1)
        cr.set_source(g)
        cr.move_to(ox, y - lh//2)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

    # ── main draw ─────────────────────────────────────────────────────────────

    def _draw(self, _w, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        self._hits.clear()

        # outer panel
        rounded_rect(cr, 0, 0, WIDGET_W, WIDGET_H, 26)
        set_rgba(cr, C_BG)
        cr.fill()
        rounded_rect(cr, 0, 0, WIDGET_W, WIDGET_H, 26)
        set_rgba(cr, C_BORDER)
        cr.set_line_width(1.5)
        cr.stroke()

        P = 14   # outer pad
        G = 10   # gap
        CW = (WIDGET_W - 2*P - 2*G) // 3  # ~202px

        R1 = 175   # row 1 height
        R2 = 160   # row 2 height
        R3 = 106   # row 3 (toggles)

        x1, x2, x3 = P, P+CW+G, P+2*(CW+G)
        y1 = P
        y2 = P + R1 + G
        y3 = P + R1 + R2 + 2*G

        self._profile_card(cr,  x1, y1, CW,       R1)
        self._clock_card(cr,    x2, y1, CW,       R1)
        self._calendar_card(cr, x3, y1, CW,       R1)
        self._music_card(cr,    x1, y2, CW*2+G,   R2)
        self._apps_card(cr,     x3, y2, CW,       R2)
        self._toggles_card(cr,  x1, y3, WIDGET_W-2*P, R3)

    # ── PROFILE ──────────────────────────────────────────────────────────────

    def _profile_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        cx = x + w//2

        # avatar
        R = 32
        ax, ay = cx, y + 20 + R
        if self._profile:
            cr.save()
            cr.arc(ax, ay, R, 0, 2*math.pi)
            cr.clip()
            Gdk.cairo_set_source_pixbuf(cr, self._profile, ax-R, ay-R)
            cr.paint()
            cr.restore()
        else:
            cr.arc(ax, ay, R, 0, 2*math.pi)
            g = cairo.RadialGradient(ax-R*0.3, ay-R*0.3, 2, ax, ay, R)
            g.add_color_stop_rgba(0, *C_PURPLE[:3], 1)
            g.add_color_stop_rgba(1, *C_BLUE[:3], 1)
            cr.set_source(g)
            cr.fill()
            self._txt(cr, "👤", ax, ay+8, 28, center=True)

        # ring
        cr.arc(ax, ay, R+2, 0, 2*math.pi)
        set_rgba(cr, C_BORDER)
        cr.set_line_width(1.5)
        cr.stroke()

        self._txt(cr, USER_NAME, cx, ay+R+22, 13, bold=True, center=True)
        wstr = f"{self.weather.icon}  {self.weather.temp}  {self.weather.desc}"
        self._txt(cr, wstr, cx, ay+R+42, 9, color=C_DIM, center=True)

    # ── CLOCK ─────────────────────────────────────────────────────────────────

    def _clock_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        now = datetime.datetime.now()
        cx  = x + w//2

        self._txt_grad(cr, now.strftime("%H:%M"), cx, y+68, size=40, center=True)
        self._txt(cr, now.strftime(":%S"), cx, y+96, 12, color=C_PURPLE, center=True)
        self._txt(cr, now.strftime("%A, %B %d"), cx, y+118, 9.5, color=C_DIM, center=True)

        # seconds arc
        R  = 26
        acx, acy = cx, y + h - 32
        cr.arc(acx, acy, R, 0, 2*math.pi)
        set_rgba(cr, C_FAINT)
        cr.set_line_width(2.5)
        cr.stroke()
        if now.second > 0:
            a0 = -math.pi/2
            a1 = a0 + (now.second/60)*2*math.pi
            cr.arc(acx, acy, R, a0, a1)
            g = cairo.LinearGradient(acx-R, acy, acx+R, acy)
            g.add_color_stop_rgba(0, *C_BLUE[:3], 1)
            g.add_color_stop_rgba(1, *C_PURPLE[:3], 1)
            cr.set_source(g)
            cr.stroke()
        da = -math.pi/2 + (now.second/60)*2*math.pi
        cr.arc(acx+R*math.cos(da), acy+R*math.sin(da), 4, 0, 2*math.pi)
        set_rgba(cr, C_PURPLE)
        cr.fill()

    # ── CALENDAR ──────────────────────────────────────────────────────────────

    def _calendar_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        today = datetime.date.today()
        first = today.replace(day=1)
        start = (first.weekday() + 1) % 7   # Sun=0

        self._txt(cr, today.strftime("%B %Y"), x+w//2, y+20, 10,
                  bold=True, color=C_PURPLE, center=True)

        cell_w = (w-16)/7
        hdr_y  = y + 36
        for i, d in enumerate(["S","M","T","W","T","F","S"]):
            self._txt(cr, d, x+8+i*cell_w+cell_w/2, hdr_y, 8,
                      color=C_FAINT, center=True)

        days_in = cal_mod.monthrange(today.year, today.month)[1]
        col, row = start, 0
        base_y = hdr_y + 16
        row_h  = (h - (base_y - y) - 8) / 5

        for d in range(1, days_in+1):
            ccx = x + 8 + col*cell_w + cell_w/2
            ccy = base_y + row*row_h + row_h/2
            if d == today.day:
                cr.arc(ccx, ccy, 10, 0, 2*math.pi)
                g = cairo.RadialGradient(ccx, ccy, 1, ccx, ccy, 10)
                g.add_color_stop_rgba(0, *C_PURPLE[:3], 0.95)
                g.add_color_stop_rgba(1, *C_BLUE[:3], 0.6)
                cr.set_source(g)
                cr.fill()
                self._txt(cr, str(d), ccx, ccy+4, 9, bold=True, center=True)
            else:
                self._txt(cr, str(d), ccx, ccy+4, 8.5, color=C_DIM, center=True)
            col += 1
            if col == 7:
                col = 0
                row += 1

    # ── MUSIC ─────────────────────────────────────────────────────────────────

    def _music_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        s = self.state

        # CD disc
        R   = 48
        dcx = x + 22 + R
        dcy = y + h//2

        cr.save()
        cr.translate(dcx, dcy)
        cr.rotate(math.radians(s.cd_angle))

        # rainbow segments
        segs = 16
        for i in range(segs):
            a1 = (i/segs)*2*math.pi
            a2 = ((i+1)/segs)*2*math.pi
            cr.move_to(0, 0)
            cr.arc(0, 0, R, a1, a2)
            cr.close_path()
            hue = i/segs
            rc = 0.45 + 0.35*math.sin(hue*2*math.pi)
            gc = 0.30 + 0.25*math.cos(hue*2*math.pi+1)
            bc = 0.75 + 0.20*math.sin(hue*2*math.pi+2)
            cr.set_source_rgba(rc, gc, bc, 0.9)
            cr.fill()

        # label ring
        cr.arc(0, 0, R*0.58, 0, 2*math.pi)
        cr.set_source_rgba(0.07, 0.06, 0.20, 1)
        cr.fill()

        # hole
        cr.arc(0, 0, R*0.11, 0, 2*math.pi)
        cr.set_source_rgba(0.20, 0.18, 0.40, 1)
        cr.fill()

        # shine
        sg = cairo.RadialGradient(-R*0.35, -R*0.35, 1, 0, 0, R)
        sg.add_color_stop_rgba(0, 1, 1, 1, 0.40)
        sg.add_color_stop_rgba(1, 1, 1, 1, 0.00)
        cr.set_source(sg)
        cr.arc(0, 0, R, 0, 2*math.pi)
        cr.fill()
        cr.restore()

        # ring border
        cr.arc(dcx, dcy, R+2, 0, 2*math.pi)
        set_rgba(cr, C_BORDER)
        cr.set_line_width(1.5)
        cr.stroke()

        # text section
        tx = dcx + R + 18
        tw = w - (tx - x) - 14

        self._txt(cr, "NOW PLAYING", tx, y+24, 7.5, color=C_FAINT)
        self._txt(cr, "YouTube", tx, y+46, 15, bold=True)
        self._txt(cr, "Open in Browser · Music", tx, y+66, 9, color=C_DIM)

        # progress bar
        bary = y + 84
        cr.rectangle(tx, bary, tw, 3)
        set_rgba(cr, C_FAINT)
        cr.fill()
        cr.rectangle(tx, bary, tw*0.38, 3)
        g = cairo.LinearGradient(tx, bary, tx+tw, bary)
        g.add_color_stop_rgba(0, *C_BLUE[:3], 1)
        g.add_color_stop_rgba(1, *C_PURPLE[:3], 1)
        cr.set_source(g)
        cr.fill()

        # control buttons
        btns = [("⏮","prev"), ("⏯" if not s.cd_playing else "⏸","play"), ("⏭","next"), ("🔗","open")]
        bw, bh = 36, 30
        gap_b  = 8
        by_b   = bary + 14

        for i, (icon, name) in enumerate(btns):
            bxb = tx + i*(bw+gap_b)
            rounded_rect(cr, bxb, by_b, bw, bh, 8)
            if name == "play":
                g = cairo.LinearGradient(bxb, by_b, bxb+bw, by_b+bh)
                g.add_color_stop_rgba(0, *C_PURPLE[:3], 0.9)
                g.add_color_stop_rgba(1, *C_BLUE[:3], 0.9)
                cr.set_source(g)
            else:
                set_rgba(cr, C_CARD)
            cr.fill()
            rounded_rect(cr, bxb, by_b, bw, bh, 8)
            set_rgba(cr, C_BORDER)
            cr.set_line_width(1)
            cr.stroke()
            self._txt(cr, icon, bxb+bw//2, by_b+bh//2+5, 14, center=True)

            def make_cb(n):
                if n == "play":
                    return lambda: setattr(self.state, "cd_playing", not self.state.cd_playing)
                elif n == "open":
                    return lambda: launch("xdg-open https://youtube.com/music")
                else:
                    return lambda: launch("xdg-open https://youtube.com")
            self._reg(f"music_{name}", bxb, by_b, bw, bh, make_cb(name))

    # ── APPS ──────────────────────────────────────────────────────────────────

    def _apps_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        self._txt(cr, "LAUNCH", x+w//2, y+20, 8, color=C_FAINT, center=True)

        cols   = 3
        rows   = math.ceil(len(APPS)/cols)
        isz    = 38
        cw     = (w-12)/cols
        row_h  = (h-32)/rows

        for i, app in enumerate(APPS):
            col = i % cols
            row = i // cols
            icx = x + 6 + col*cw + cw/2
            icy = y + 30 + row*row_h + row_h/2 - 10

            rounded_rect(cr, icx-isz/2, icy-isz/2, isz, isz, 10)
            set_rgba(cr, C_CARD)
            cr.fill()
            rounded_rect(cr, icx-isz/2, icy-isz/2, isz, isz, 10)
            set_rgba(cr, C_BORDER)
            cr.set_line_width(1)
            cr.stroke()

            self._txt(cr, app["icon"], icx, icy+8, 18, center=True)
            self._txt(cr, app["name"], icx, icy+isz/2+14, 8, color=C_DIM, center=True)

            cmd = app["cmd"]
            self._reg(f"app_{i}", icx-isz/2, icy-isz/2, isz, isz+18,
                      lambda c=cmd: launch(c))

    # ── TOGGLES ───────────────────────────────────────────────────────────────

    def _toggles_card(self, cr, x, y, w, h):
        glass_card(cr, x, y, w, h)
        s = self.state

        items = [
            ("📶", "Wi-Fi",     "wifi",   s.wifi,   self._t_wifi),
            ("🦷", "Bluetooth", "bt",     s.bt,     self._t_bt),
            ("🌙", "Night",     "night",  s.night,  self._t_night),
            ("🔆", "Bright",    "bright", s.bright, self._t_bright),
            ("⚡", "Power",     "power",  False,    self._t_power),
        ]

        bw, bh = 52, 52
        n = len(items)
        spacing = (w-16)/n
        by = y + (h-bh)//2 - 8

        for i, (icon, label, key, active, cb) in enumerate(items):
            bx = x + 8 + i*spacing + (spacing-bw)/2
            rounded_rect(cr, bx, by, bw, bh, 14)
            if active:
                g = cairo.LinearGradient(bx, by, bx+bw, by+bh)
                g.add_color_stop_rgba(0, *C_PURPLE[:3], 0.32)
                g.add_color_stop_rgba(1, *C_BLUE[:3], 0.22)
                cr.set_source(g)
            else:
                set_rgba(cr, C_CARD)
            cr.fill()
            rounded_rect(cr, bx, by, bw, bh, 14)
            set_rgba(cr, C_PURPLE if active else C_BORDER)
            cr.set_line_width(1.5)
            cr.stroke()

            self._txt(cr, icon, bx+bw/2, by+bh/2+7, 22, center=True)
            self._txt(cr, label, bx+bw/2, by+bh+18, 8.5,
                      color=C_PURPLE if active else C_DIM, center=True)
            self._reg(f"tog_{key}", bx, by, bw, bh+22, cb)

    def _t_wifi(self):
        s = self.state
        run_cmd("nmcli radio wifi " + ("off" if s.wifi else "on"))
        s.wifi = not s.wifi

    def _t_bt(self):
        s = self.state
        run_cmd("bluetoothctl power " + ("off" if s.bt else "on"))
        s.bt = not s.bt

    def _t_night(self):
        s = self.state
        s.night = not s.night
        run_cmd("redshift -O 3500" if s.night else "redshift -x")

    def _t_bright(self):
        s = self.state
        s.bright = not s.bright
        run_cmd("brightnessctl set " + ("100%" if s.bright else "40%"))

    def _t_power(self):
        d = Gtk.MessageDialog(parent=None, flags=0,
                              message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.NONE,
                              text="Power Options")
        d.add_button("Suspend",  1)
        d.add_button("Restart",  2)
        d.add_button("Shutdown", 3)
        d.add_button("Cancel",   0)
        r = d.run(); d.destroy()
        if r == 1: run_cmd("systemctl suspend")
        elif r == 2: run_cmd("systemctl reboot")
        elif r == 3: run_cmd("systemctl poweroff")


# ─── RUN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    w = Widget()
    w.connect("destroy", Gtk.main_quit)
    Gtk.main()
