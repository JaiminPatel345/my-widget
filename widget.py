#!/usr/bin/env python3
"""
Desktop Widget — Axarva-inspired dark panel for Ubuntu
3-column layout:
  LEFT:   Profile + weather + toggles + quote
  CENTER: Clock+Calendar | Music | Search bar
  RIGHT:  App launcher (rows) + System buttons (2×3 grid)
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo, GdkPixbuf
import cairo
import subprocess
import threading
import datetime
import math
import os
import random
import colorsys

# ─────────────────────────────────────────────
#  USER CONFIG — edit these
# ─────────────────────────────────────────────
DISPLAY_NAME  = "Jaimin Detroja"
PROFILE_IMAGE = os.path.expanduser("~/Pictures/profile.jpg")
CITY          = "Vadodara"   # or e.g. "Mumbai"

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────
BG     = (0.07, 0.07, 0.09, 0.96)
CARD   = (0.10, 0.10, 0.13, 1.00)
CARD2  = (0.13, 0.13, 0.17, 1.00)
BORDER = (1.0,  1.0,  1.0,  0.06)
PINK   = (0.92, 0.42, 0.62, 1.00)
CYAN   = (0.40, 0.85, 0.85, 1.00)
WHITE  = (1.0,  1.0,  1.0,  1.00)
GREY   = (1.0,  1.0,  1.0,  0.55)
DIM    = (1.0,  1.0,  1.0,  0.28)
RED    = (0.90, 0.35, 0.45, 1.00)
GREEN  = (0.35, 0.85, 0.55, 1.00)
ORANGE = (1.00, 0.65, 0.30, 1.00)
PURPLE = (0.60, 0.35, 0.90, 1.00)

QUOTES = [
    ("Wisdom begins in wonder.", "Socrates"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("Code is poetry.", "WordPress"),
    ("First, solve the problem.", "John Johnson"),
    ("Make it work, then beautiful.", "Joe Armstrong"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Programs must be written for people.", "Harold Abelson"),
]

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ══════════════════════════════════════════════════════════
#  CAIRO HELPERS
# ══════════════════════════════════════════════════════════
def rr(cr, x, y, w, h, r=12):
    cr.new_sub_path()
    cr.arc(x+r,   y+r,   r, math.pi,     1.5*math.pi)
    cr.arc(x+w-r, y+r,   r, 1.5*math.pi, 0)
    cr.arc(x+w-r, y+h-r, r, 0,           0.5*math.pi)
    cr.arc(x+r,   y+h-r, r, 0.5*math.pi, math.pi)
    cr.close_path()

def draw_card(cr, x, y, w, h, r=14, bg=None):
    c = bg or CARD
    rr(cr, x, y, w, h, r)
    cr.set_source_rgba(*c)
    cr.fill_preserve()
    cr.set_source_rgba(*BORDER)
    cr.set_line_width(1)
    cr.stroke()

def sc(cr, c):
    cr.set_source_rgba(*c)


# ══════════════════════════════════════════════════════════
#  ICON LOADER — loads real system icons via GTK icon theme
# ══════════════════════════════════════════════════════════
_icon_cache = {}

def load_icon(name, size=48):
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]

    theme = Gtk.IconTheme.get_default()
    candidates = [
        name, name.lower(),
        name.replace("-","_"), name.replace("_","-"),
        f"{name}-symbolic",
        f"application-x-{name}",
    ]
    for c in candidates:
        try:
            pb = theme.load_icon(c, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if pb:
                surf = _pb_to_surface(pb)
                _icon_cache[key] = surf
                return surf
        except Exception:
            pass

    # Search common filesystem paths
    search_paths = [
        f"/usr/share/icons/hicolor/{size}x{size}/apps/{name}.png",
        f"/usr/share/icons/hicolor/256x256/apps/{name}.png",
        f"/usr/share/icons/hicolor/scalable/apps/{name}.svg",
        f"/usr/share/pixmaps/{name}.png",
        f"/usr/share/pixmaps/{name}.xpm",
        f"/opt/{name}/icons/hicolor/48x48/apps/{name}.png",
        f"/snap/{name}/current/meta/gui/icon.png",
    ]
    for p in search_paths:
        if os.path.exists(p):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, size, size, True)
                surf = _pb_to_surface(pb)
                _icon_cache[key] = surf
                return surf
            except Exception:
                pass

    _icon_cache[key] = None
    return None

def _pb_to_surface(pb):
    w, h = pb.get_width(), pb.get_height()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr   = cairo.Context(surf)
    Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
    cr.paint()
    return surf

def blit_icon(cr, surf, cx, cy, size):
    if surf is None:
        return
    sw, sh = surf.get_width(), surf.get_height()
    scale  = size / max(sw, sh)
    cr.save()
    cr.translate(cx - sw*scale/2, cy - sh*scale/2)
    cr.scale(scale, scale)
    cr.set_source_surface(surf, 0, 0)
    cr.paint()
    cr.restore()

def color_initial_icon(cr, cx, cy, r, letter, color):
    """Fallback: draw a colored circle with initial letter."""
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgba(*color[:3], 0.25)
    cr.fill()
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgba(*color[:3], 0.7)
    cr.set_line_width(1.5)
    cr.stroke()
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(r*0.95)
    e = cr.text_extents(letter)
    sc(cr, WHITE)
    cr.move_to(cx - e.width/2, cy + e.height/2)
    cr.show_text(letter)


# ══════════════════════════════════════════════════════════
#  LEFT PANEL — Profile, Weather, Toggles, Quote
# ══════════════════════════════════════════════════════════
class LeftPanel(Gtk.DrawingArea):
    PW, PH = 300, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._weather   = "Fetching…"
        self._temp      = "--°C"
        self._condition = ""
        self._wicon     = "🌤"
        self._quote, self._author = random.choice(QUOTES)
        self._profile   = self._load_profile()
        self._tog_states = [False, False, False, True]  # wifi,bt,night,bright
        self._hover_tog = -1
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("draw",                self._draw)
        self.connect("button-press-event",  self._on_click)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event",  self._on_leave)
        GLib.timeout_add(2000, lambda: (self.queue_draw(), True)[1])
        threading.Thread(target=self._fetch_weather, daemon=True).start()
        threading.Thread(target=self._detect_states, daemon=True).start()

    def _load_profile(self):
        for p in [PROFILE_IMAGE,
                  os.path.expanduser("~/Pictures/profile.png"),
                  os.path.expanduser("~/Pictures/avatar.jpg")]:
            if os.path.exists(p):
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, 130, 130, True)
                    return _pb_to_surface(pb)
                except Exception:
                    pass
        return None

    def _detect_states(self):
        try:
            out = subprocess.check_output(["nmcli","radio","wifi"],
                                           stderr=subprocess.DEVNULL).decode().strip()
            self._tog_states[0] = (out == "enabled")
        except: pass
        try:
            out = subprocess.check_output(["bluetoothctl","show"],
                                           stderr=subprocess.DEVNULL).decode()
            self._tog_states[1] = "Powered: yes" in out
        except: pass
        GLib.idle_add(self.queue_draw)

    def _fetch_weather(self):
        if not HAS_REQUESTS:
            self._temp = "--°C"; self._condition = "install requests"
            GLib.idle_add(self.queue_draw); return
        try:
            data = requests.get(f"https://wttr.in/{CITY}?format=j1", timeout=6).json()
            cur  = data["current_condition"][0]
            self._temp      = cur["temp_C"] + "°C"
            self._condition = cur["weatherDesc"][0]["value"]
            code = int(cur["weatherCode"])
            M = {113:"☀️",116:"⛅",119:"☁️",122:"☁️",176:"🌦",
                 200:"⛈",227:"❄️",263:"🌦",293:"🌧",356:"🌧",389:"⛈"}
            self._wicon = M.get(code, "🌤")
        except:
            self._temp = "--°C"; self._condition = "Unavailable"
        GLib.idle_add(self.queue_draw)

    TOG_DEFS = [
        ("Wi-Fi",     "network-wireless",
         ["nmcli","radio","wifi","off"], ["nmcli","radio","wifi","on"]),
        ("Bluetooth", "bluetooth",
         ["bluetoothctl","power","off"],["bluetoothctl","power","on"]),
        ("Night",     "weather-clear-night",
         ["redshift","-x"],              ["redshift","-O","3500"]),
        ("Bright",    "display-brightness-high",
         ["xrandr","--brightness","1"],  ["xrandr","--brightness","0.6"]),
    ]

    def _tog_rect(self, i):
        pad = 12
        n   = len(self.TOG_DEFS)
        bw  = (self.PW - pad*2 - (n-1)*6) / n
        bh  = 60
        y   = self.PH - 160
        return pad + i*(bw+6), y, bw, bh

    def _on_click(self, w, event):
        for i in range(len(self.TOG_DEFS)):
            x, y, bw, bh = self._tog_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh:
                self._tog_states[i] = not self._tog_states[i]
                on  = self._tog_states[i]
                cmd = self.TOG_DEFS[i][3] if on else self.TOG_DEFS[i][2]
                subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
                self.queue_draw()
                return

    def _on_motion(self, w, event):
        h = -1
        for i in range(len(self.TOG_DEFS)):
            x, y, bw, bh = self._tog_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh: h=i; break
        if h != self._hover_tog:
            self._hover_tog = h; self.queue_draw()

    def _on_leave(self, *_):
        if self._hover_tog != -1:
            self._hover_tog = -1; self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad  = 12

        draw_card(cr, 0, 0, w, h, 16, CARD)

        # ── Profile ──
        img_cx, img_cy, img_r = w//2, 95, 56
        cr.save()
        cr.arc(img_cx, img_cy, img_r, 0, 2*math.pi)
        cr.clip()
        if self._profile:
            sw = self._profile.get_width()
            sh = self._profile.get_height()
            sc_ = (img_r*2) / min(sw, sh)
            cr.translate(img_cx - sw*sc_/2, img_cy - sh*sc_/2)
            cr.scale(sc_, sc_)
            cr.set_source_surface(self._profile, 0, 0)
        else:
            g = cairo.RadialGradient(img_cx, img_cy-20, 0, img_cx, img_cy, img_r)
            g.add_color_stop_rgba(0, *PINK[:3], 1)
            g.add_color_stop_rgba(1, *PURPLE[:3], 1)
            cr.set_source(g)
        cr.paint()
        cr.restore()
        cr.arc(img_cx, img_cy, img_r+2.5, 0, 2*math.pi)
        sc(cr, PINK); cr.set_line_width(2.5); cr.stroke()

        # Name
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(20)
        sc(cr, PINK)
        ne = cr.text_extents(DISPLAY_NAME)
        cr.move_to(w/2 - ne.width/2, 183); cr.show_text(DISPLAY_NAME)

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, GREY)
        sub = "That Developer"
        se = cr.text_extents(sub)
        cr.move_to(w/2 - se.width/2, 200); cr.show_text(sub)

        # Divider
        sc(cr, BORDER); cr.set_line_width(1)
        cr.move_to(pad, 212); cr.line_to(w-pad, 212); cr.stroke()

        # ── Weather ──
        draw_card(cr, pad, 220, w-pad*2, 96, 12, CARD2)
        cr.set_font_size(36)
        cr.move_to(pad+16, 220+60); sc(cr, WHITE)
        cr.show_text(self._wicon)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(28); sc(cr, WHITE)
        cr.move_to(pad+70, 220+48); cr.show_text(self._temp)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, PINK)
        cr.move_to(pad+70, 220+66); cr.show_text(self._condition[:22])
        msgs = {"Clear":"Perfect day outside! ☀️","Sunny":"Go for a walk! 🌞",
                "Cloud":"Maybe bring a jacket.","Rain":"Grab your umbrella! 🌂",
                "Snow":"Stay warm and cozy! ❄️"}
        msg = next((v for k,v in msgs.items()
                    if k.lower() in self._condition.lower()), "Have a great day! ✨")
        cr.set_font_size(10); sc(cr, GREY)
        me = cr.text_extents(msg)
        cr.move_to(w/2 - me.width/2, 220+86); cr.show_text(msg)

        # ── Toggles ──
        for i, (lbl, icon_name, off_c, on_c) in enumerate(self.TOG_DEFS):
            x, y, bw, bh = self._tog_rect(i)
            is_on = self._tog_states[i]
            is_h  = (i == self._hover_tog)
            ac    = PINK if is_on else (GREY if is_h else DIM)

            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*PINK[:3], 0.18 if is_on else (0.08 if is_h else 0.04))
            cr.fill()
            if is_on or is_h:
                rr(cr, x, y, bw, bh, 10)
                sc(cr, PINK if is_on else (0.5,0.5,0.5,0.5))
                cr.set_line_width(1.5 if is_on else 1); cr.stroke()

            # Icon
            isurf = load_icon(icon_name, 24)
            if isurf:
                cr.save()
                if not is_on:
                    cr.set_source_rgba(0.5,0.5,0.5,0.7)
                    rr(cr, x, y, bw, bh, 10); cr.clip()
                blit_icon(cr, isurf, x+bw/2, y+bh/2-8, 22)
                cr.restore()
            else:
                fb = {"Wi-Fi":"📶","Bluetooth":"🔷","Night":"🌙","Bright":"☀️"}
                cr.set_font_size(18)
                fbe = cr.text_extents(fb.get(lbl,"●"))
                sc(cr, PINK if is_on else GREY)
                cr.move_to(x+bw/2-fbe.width/2, y+bh/2-2); cr.show_text(fb.get(lbl,"●"))

            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(9); sc(cr, ac)
            le = cr.text_extents(lbl)
            cr.move_to(x+bw/2-le.width/2, y+bh-8); cr.show_text(lbl)

        # ── Quote ──
        q_y = self.PH - 90
        draw_card(cr, pad, q_y, w-pad*2, 78, 12, CARD2)
        cr.select_font_face("Serif", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, GREY)
        words = self._quote.split()
        lines, line = [], ""
        for word in words:
            test = (line+" "+word).strip()
            if cr.text_extents(test).width < w-pad*2-20:
                line = test
            else:
                lines.append(line); line = word
        if line: lines.append(line)
        for li, ln in enumerate(lines[:3]):
            cr.move_to(pad+10, q_y+16+li*14); cr.show_text(ln)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10); sc(cr, PINK)
        auth = f"— {self._author}"
        ae = cr.text_extents(auth)
        cr.move_to(w-pad-ae.width-6, q_y+66); cr.show_text(auth)


# ══════════════════════════════════════════════════════════
#  CENTER PANEL — Clock+Calendar | Music | Search
# ══════════════════════════════════════════════════════════
class CenterPanel(Gtk.DrawingArea):
    PW, PH = 430, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._now      = datetime.datetime.now()
        self._angle    = 0.0
        self._playing  = False
        self._title    = "YouTube"
        self._artist   = "Open in Browser · Music"
        self._progress = 0.0
        self._marquee  = 0
        self._search   = ""
        self._sfocus   = False
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        self.set_can_focus(True)
        self.connect("draw",               self._draw)
        self.connect("button-press-event", self._on_click)
        self.connect("key-press-event",    self._on_key)
        GLib.timeout_add(1000, self._clock_tick)
        GLib.timeout_add(50,   self._anim_tick)
        GLib.timeout_add(2000, self._poll_player)
        self._poll_player()

    def _clock_tick(self):
        self._now = datetime.datetime.now()
        self.queue_draw(); return True

    def _anim_tick(self):
        if self._playing:
            self._angle    += 0.025
            self._marquee  += 1
            self._progress  = (self._progress + 0.001) % 1.0
        self.queue_draw(); return True

    def _poll_player(self):
        def _do():
            try:
                s = subprocess.check_output(
                    ["playerctl","status"], stderr=subprocess.DEVNULL).decode().strip()
                self._playing = (s == "Playing")
                t = subprocess.check_output(
                    ["playerctl","metadata","title"], stderr=subprocess.DEVNULL).decode().strip()
                a = subprocess.check_output(
                    ["playerctl","metadata","artist"], stderr=subprocess.DEVNULL).decode().strip()
                self._title  = t or "YouTube"
                self._artist = a or "Open in Browser · Music"
            except:
                self._playing = False
                self._title   = "YouTube"
                self._artist  = "Open in Browser · Music"
            GLib.idle_add(self.queue_draw)
        threading.Thread(target=_do, daemon=True).start()
        return True

    def _on_click(self, widget, event):
        self.grab_focus()
        x, y = event.x, event.y
        w, h = self.PW, self.PH

        # Music controls (y ~370-420)
        ctl_y = h - 170
        pad   = 14
        cw    = w - pad*2
        ctl_cx = pad + cw/2

        if abs(y - ctl_y) < 26:
            if abs(x-(ctl_cx-70)) < 22: subprocess.Popen(["playerctl","previous"])
            elif abs(x-(ctl_cx-24)) < 22:
                subprocess.Popen(["playerctl","play-pause"])
                self._playing = not self._playing
            elif abs(x-(ctl_cx+22)) < 22: subprocess.Popen(["playerctl","next"])
            elif abs(x-(ctl_cx+68)) < 22:
                subprocess.Popen(["xdg-open","https://youtube.com"])
            self.queue_draw()

        # Search bar
        s_y = h - 62
        if y > s_y - 4 and y < h - 8:
            self._sfocus = True; self.queue_draw()

    def _on_key(self, widget, event):
        if not self._sfocus: return
        k = event.keyval
        if k == Gdk.KEY_Return:
            q = self._search.strip()
            if q:
                subprocess.Popen(["xdg-open",
                    f"https://google.com/search?q={q.replace(' ','+')}"])
            self._search = ""; self._sfocus = False
        elif k == Gdk.KEY_Escape:
            self._search = ""; self._sfocus = False
        elif k == Gdk.KEY_BackSpace:
            self._search = self._search[:-1]
        else:
            ch = event.string
            if ch and ch.isprintable(): self._search += ch
        self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad  = 14
        cw   = w - pad*2

        # ── TOP ROW: Clock card + Calendar card ──
        clock_w = 180
        cal_w   = cw - clock_w - 8
        top_h   = 200

        draw_card(cr, pad, 0, clock_w, top_h, 14, CARD)
        self._draw_clock(cr, pad, 0, clock_w, top_h)

        draw_card(cr, pad+clock_w+8, 0, cal_w, top_h, 14, CARD)
        self._draw_calendar(cr, pad+clock_w+8, 0, cal_w, top_h)

        # ── MUSIC card ──
        mus_y = top_h + 10
        mus_h = h - top_h - 10 - 78
        draw_card(cr, pad, mus_y, cw, mus_h, 14, CARD)
        self._draw_music(cr, pad, mus_y, cw, mus_h)

        # ── SEARCH BAR ──
        s_y = h - 68
        s_h = 60
        draw_card(cr, pad, s_y, cw, s_h, 14, CARD2)
        self._draw_search(cr, pad, s_y, cw, s_h)

    def _draw_clock(self, cr, ox, oy, w, h):
        now = self._now
        cx  = ox + w/2

        # Big HH:MM
        cr.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(42)
        ts = now.strftime("%H:%M")
        te = cr.text_extents(ts)
        sc(cr, WHITE)
        cr.move_to(cx - te.width/2, oy+52); cr.show_text(ts)

        # Seconds (pink, smaller)
        cr.set_font_size(14); sc(cr, PINK)
        ss = ":" + now.strftime("%S")
        se = cr.text_extents(ss)
        cr.move_to(cx + te.width/2 + 2, oy+52); cr.show_text(ss)

        # Date
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, GREY)
        ds = now.strftime("%A, %B %d")
        de = cr.text_extents(ds)
        cr.move_to(cx - de.width/2, oy+68); cr.show_text(ds)

        # Analog clock
        acx, acy, acr = cx, oy+h-46, 38
        cr.arc(acx, acy, acr, 0, 2*math.pi)
        cr.set_source_rgba(0.06,0.06,0.09,1); cr.fill()
        cr.arc(acx, acy, acr, 0, 2*math.pi)
        sc(cr, BORDER); cr.set_line_width(1); cr.stroke()

        for i in range(12):
            a = i*math.pi/6 - math.pi/2
            d = acr-5
            cr.arc(acx+d*math.cos(a), acy+d*math.sin(a), 1.5, 0, 2*math.pi)
            sc(cr, DIM); cr.fill()

        def hand(ang, L, lw, col):
            cr.set_line_width(lw); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            sc(cr, col)
            cr.move_to(acx, acy)
            cr.line_to(acx+L*math.cos(ang-math.pi/2), acy+L*math.sin(ang-math.pi/2))
            cr.stroke()

        t = now
        hand((t.hour%12 + t.minute/60)*math.pi/6,   acr*0.52, 2.5, WHITE)
        hand((t.minute + t.second/60)*math.pi/30,    acr*0.72, 1.8, GREY)
        hand(t.second*math.pi/30,                    acr*0.82, 1.2, PINK)
        cr.arc(acx, acy, 3, 0, 2*math.pi); sc(cr, PINK); cr.fill()

    def _draw_calendar(self, cr, ox, oy, w, h):
        import calendar
        now = self._now
        pad = 10

        # Month header
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(13); sc(cr, CYAN)
        ms = now.strftime("%B %Y")
        me = cr.text_extents(ms)
        cr.move_to(ox+w/2-me.width/2, oy+18); cr.show_text(ms)

        days_hdr = ["S","M","T","W","T","F","S"]
        cell = (w-pad*2)/7
        cr.set_font_size(9)
        for i, d in enumerate(days_hdr):
            sc(cr, PINK if i in(0,6) else DIM)
            de = cr.text_extents(d)
            cr.move_to(ox+pad+i*cell+cell/2-de.width/2, oy+32); cr.show_text(d)

        first_wd, num_days = calendar.monthrange(now.year, now.month)
        col = (first_wd+1)%7
        row = 0
        cr.set_font_size(9)
        for day in range(1, num_days+1):
            dcx = ox+pad+col*cell+cell/2
            dcy = oy+46+row*20
            if day == now.day:
                cr.arc(dcx, dcy-3, 9, 0, 2*math.pi)
                sc(cr, CYAN); cr.fill()
                sc(cr, (0.07,0.07,0.09,1))
            else:
                sc(cr, PINK if col in(0,6) else GREY)
            de = cr.text_extents(str(day))
            cr.move_to(dcx-de.width/2, dcy); cr.show_text(str(day))
            col += 1
            if col == 7: col=0; row+=1

    def _draw_music(self, cr, ox, oy, w, h):
        pad = 16
        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9); sc(cr, DIM)
        cr.move_to(ox+pad, oy+14); cr.show_text("NOW PLAYING")

        # Spinning disc
        disk_cx = ox + pad + 58
        disk_cy = oy + h//2 + 4
        disk_r  = 54

        cr.save()
        cr.translate(disk_cx, disk_cy)
        cr.rotate(self._angle)
        for i in range(12):
            a0 = i*2*math.pi/12
            a1 = (i+1)*2*math.pi/12
            hv = (i/12 + self._angle/(2*math.pi)) % 1.0
            r_, g_, b_ = colorsys.hsv_to_rgb(hv*0.3+0.7, 0.75, 0.65)
            cr.move_to(0,0); cr.arc(0,0,disk_r,a0,a1)
            cr.set_source_rgba(r_,g_,b_,0.88); cr.fill()
        for gr in [0.38,0.58,0.78,0.92]:
            cr.arc(0,0,disk_r*gr,0,2*math.pi)
            cr.set_source_rgba(0,0,0,0.35); cr.set_line_width(1); cr.stroke()
        cr.arc(0,0,15,0,2*math.pi)
        cr.set_source_rgba(0.07,0.07,0.09,1); cr.fill()
        cr.arc(0,0,15,0,2*math.pi)
        sc(cr,PINK); cr.set_line_width(2); cr.stroke()
        cr.arc(0,0,4,0,2*math.pi); sc(cr,PINK); cr.fill()
        cr.restore()

        # Waveform if playing
        if self._playing:
            wx = disk_cx + disk_r + 10
            for i in range(14):
                t  = self._angle*3 + i*0.45
                bh = 6+14*abs(math.sin(t))
                by = disk_cy - bh/2
                al = 0.3+0.7*abs(math.sin(t))
                cr.set_source_rgba(*PINK[:3], al)
                rr(cr, wx+i*7, by, 4, bh, 2); cr.fill()

        # Text
        tx = ox + pad + 58*2 + 20
        tw = w - (tx-ox) - pad

        title = self._title
        if len(title) > 20:
            off = (self._marquee//3)%(len(title)+5)
            padded = title+"     "
            title = (padded*2)[off:off+20]

        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(18); sc(cr, WHITE)
        cr.move_to(tx, oy+50); cr.show_text(title[:20])

        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11); sc(cr, GREY)
        cr.move_to(tx, oy+68); cr.show_text(self._artist[:26])

        # Progress
        pb_y = oy+82; pb_h=4
        rr(cr, tx, pb_y, tw, pb_h, 2)
        cr.set_source_rgba(1,1,1,0.1); cr.fill()
        if self._progress > 0:
            rr(cr, tx, pb_y, max(6,tw*self._progress), pb_h, 2)
            sc(cr, PINK); cr.fill()

        # Controls
        ctl_y = oy + h - 44
        ctl_cx = tx + tw/2
        btns = [
            (ctl_cx-70, "⏮", 14, False),
            (ctl_cx-24, "⏸" if self._playing else "▶", 20, True),
            (ctl_cx+22, "⏭", 14, False),
            (ctl_cx+68, "🔗", 13, False),
        ]
        for bx, icon, size, is_play in btns:
            if is_play:
                rr(cr, bx-18, ctl_y-18, 36, 36, 8)
                cr.set_source_rgba(*PINK[:3],0.2); cr.fill()
                rr(cr, bx-18, ctl_y-18, 36, 36, 8)
                sc(cr, PINK); cr.set_line_width(1.5); cr.stroke()
            cr.set_font_size(size)
            e = cr.text_extents(icon)
            sc(cr, PINK if is_play else GREY)
            cr.move_to(bx-e.width/2, ctl_y+e.height/2); cr.show_text(icon)

    def _draw_search(self, cr, ox, oy, w, h):
        pad = 14
        cr.set_font_size(16); sc(cr, GREY)
        cr.move_to(ox+pad+4, oy+h/2+6); cr.show_text("🔍")
        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(13)
        if self._search:
            sc(cr, WHITE)
            disp = self._search+("│" if self._sfocus else "")
            cr.move_to(ox+pad+30, oy+h/2+5); cr.show_text(disp[-32:])
        else:
            sc(cr, DIM)
            cr.move_to(ox+pad+30, oy+h/2+5)
            cr.show_text("Search the web…  (click here, then type)")
        if self._sfocus:
            rr(cr, ox, oy, w, h, 14); sc(cr, PINK)
            cr.set_line_width(1.5); cr.stroke()


# ══════════════════════════════════════════════════════════
#  RIGHT PANEL — App Launcher rows + System 2×3 grid
# ══════════════════════════════════════════════════════════
APP_DEFS = [
    {"name":"Chrome",   "icon":"google-chrome",  "cmd":"google-chrome",
     "color":CYAN},
    {"name":"Brave",    "icon":"brave-browser",  "cmd":"brave-browser",
     "color":ORANGE},
    {"name":"Discord",  "icon":"discord",        "cmd":"discord",
     "color":(0.35,0.40,0.90,1)},
    {"name":"Teams",    "icon":"teams-for-linux","cmd":"teams-for-linux",
     "color":(0.28,0.40,0.82,1)},
    {"name":"VSCode",   "icon":"code",           "cmd":"code",
     "color":(0.14,0.53,0.90,1)},
    {"name":"WebStorm", "icon":"webstorm",       "cmd":"webstorm.sh",
     "color":PINK},
]

SYS_DEFS = [
    {"icon":"image-x-generic",    "tip":"Gallery",   "cmd":["eog"],
     "color":GREY},
    {"icon":"system-shutdown",    "tip":"Shutdown",  "cmd":["systemctl","poweroff"],
     "color":RED,  "confirm":True},
    {"icon":"view-refresh",       "tip":"Restart",   "cmd":["systemctl","reboot"],
     "color":CYAN, "confirm":True},
    {"icon":"system-lock-screen", "tip":"Lock",      "cmd":["gnome-screensaver-command","--lock"],
     "color":GREY},
    {"icon":"weather-clear-night","tip":"Night",     "cmd":["redshift","-O","3500"],
     "color":PURPLE},
    {"icon":"system-log-out",     "tip":"Logout",    "cmd":["gnome-session-quit","--logout","--no-prompt"],
     "color":ORANGE, "confirm":True},
]

class RightPanel(Gtk.DrawingArea):
    PW, PH = 220, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._ha = -1   # hover app
        self._hs = -1   # hover sys
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("draw",                self._draw)
        self.connect("button-press-event",  self._on_click)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event",  self._on_leave)
        # Pre-load icons
        threading.Thread(target=self._preload, daemon=True).start()

    def _preload(self):
        for a in APP_DEFS: load_icon(a["icon"], 48)
        for s in SYS_DEFS: load_icon(s["icon"], 36)
        GLib.idle_add(self.queue_draw)

    PAD = 10

    def _app_rect(self, i):
        bw = self.PW - self.PAD*2
        bh = 46
        return self.PAD, 18 + i*(bh+6), bw, bh

    def _sys_rect(self, i):
        apps_bot = 18 + len(APP_DEFS)*(46+6) + 10
        bw = (self.PW - self.PAD*2 - 6)//2
        bh = 58
        col = i%2; row = i//2
        return self.PAD + col*(bw+6), apps_bot+14+row*(bh+6), bw, bh

    def _on_click(self, w, event):
        for i, app in enumerate(APP_DEFS):
            x,y,bw,bh = self._app_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh:
                try: subprocess.Popen(app["cmd"].split())
                except Exception as e: print(f"Launch error: {e}")
                return
        for i, btn in enumerate(SYS_DEFS):
            x,y,bw,bh = self._sys_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh:
                if btn.get("confirm"):
                    d = Gtk.MessageDialog(
                        message_type=Gtk.MessageType.WARNING,
                        buttons=Gtk.ButtonsType.OK_CANCEL,
                        text=f"{btn['tip']}?")
                    r = d.run(); d.destroy()
                    if r != Gtk.ResponseType.OK: return
                try: subprocess.Popen(btn["cmd"])
                except Exception as e: print(f"Sys error: {e}")
                return

    def _on_motion(self, w, event):
        ha, hs = -1, -1
        for i in range(len(APP_DEFS)):
            x,y,bw,bh = self._app_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh: ha=i; break
        for i in range(len(SYS_DEFS)):
            x,y,bw,bh = self._sys_rect(i)
            if x<=event.x<=x+bw and y<=event.y<=y+bh: hs=i; break
        if ha!=self._ha or hs!=self._hs:
            self._ha=ha; self._hs=hs; self.queue_draw()

    def _on_leave(self, *_):
        self._ha=self._hs=-1; self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad  = self.PAD

        draw_card(cr, 0, 0, w, h, 16, CARD)

        # LAUNCH label
        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9); sc(cr, DIM)
        cr.move_to(pad, 13); cr.show_text("LAUNCH")

        # App rows
        for i, app in enumerate(APP_DEFS):
            x, y, bw, bh = self._app_rect(i)
            is_h = (i == self._ha)
            ac   = app["color"]

            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*ac[:3], 0.18 if is_h else 0.04); cr.fill()
            if is_h:
                rr(cr, x, y, bw, bh, 10)
                cr.set_source_rgba(*ac[:3], 0.55)
                cr.set_line_width(1); cr.stroke()

            isurf = load_icon(app["icon"], 48)
            if isurf:
                blit_icon(cr, isurf, x+26, y+bh/2, 30)
            else:
                color_initial_icon(cr, x+26, y+bh/2, 14, app["name"][0], ac)

            cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(13)
            sc(cr, WHITE if is_h else GREY)
            cr.move_to(x+50, y+bh/2+5); cr.show_text(app["name"])

            if is_h:
                cr.set_font_size(14); sc(cr, ac)
                cr.move_to(x+bw-14, y+bh/2+5); cr.show_text("›")

        # Divider
        sep_y = 18 + len(APP_DEFS)*(46+6) + 2
        sc(cr, BORDER); cr.set_line_width(1)
        cr.move_to(pad, sep_y); cr.line_to(w-pad, sep_y); cr.stroke()

        # SYSTEM label
        cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9); sc(cr, DIM)
        cr.move_to(pad, sep_y+12); cr.show_text("SYSTEM")

        # System 2×3 grid
        SYS_FB = {
            "image-x-generic":"🖼",
            "system-shutdown":"⏻",
            "view-refresh":"↺",
            "system-lock-screen":"🔒",
            "weather-clear-night":"🌙",
            "system-log-out":"⇥",
        }
        for i, btn in enumerate(SYS_DEFS):
            x, y, bw, bh = self._sys_rect(i)
            is_h = (i == self._hs)
            bc   = btn["color"]

            rr(cr, x, y, bw, bh, 10)
            cr.set_source_rgba(*bc[:3], 0.20 if is_h else 0.05); cr.fill()
            if is_h:
                rr(cr, x, y, bw, bh, 10)
                sc(cr, bc); cr.set_line_width(1.5); cr.stroke()

            isurf = load_icon(btn["icon"], 36)
            if isurf:
                blit_icon(cr, isurf, x+bw/2, y+bh/2-6, 28)
            else:
                cr.set_font_size(22)
                fb = SYS_FB.get(btn["icon"],"●")
                fe = cr.text_extents(fb)
                sc(cr, bc if is_h else GREY)
                cr.move_to(x+bw/2-fe.width/2, y+bh/2); cr.show_text(fb)

            cr.set_font_size(9)
            cr.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
            sc(cr, bc if is_h else DIM)
            te = cr.text_extents(btn["tip"])
            cr.move_to(x+bw/2-te.width/2, y+bh-7); cr.show_text(btn["tip"])


# ══════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════
class DesktopWidget(Gtk.Window):

    def __init__(self):
        super().__init__()
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(True)
        self.set_app_paintable(True)
        self.set_resizable(False)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual: self.set_visual(visual)

        total_w = LeftPanel.PW + 12 + CenterPanel.PW + 12 + RightPanel.PW + 48
        total_h = max(LeftPanel.PH, CenterPanel.PH, RightPanel.PH) + 48
        self.set_default_size(total_w, total_h)

        sw, sh = screen.get_width(), screen.get_height()
        self.move((sw-total_w)//2, (sh-total_h)//2)

        outer = Gtk.DrawingArea()
        outer.set_size_request(total_w, total_h)
        outer.connect("draw", self._draw_bg)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(24); hbox.set_margin_bottom(24)
        hbox.set_margin_start(24); hbox.set_margin_end(24)
        hbox.pack_start(LeftPanel(),   False, False, 0)
        hbox.pack_start(CenterPanel(), False, False, 0)
        hbox.pack_start(RightPanel(),  False, False, 0)

        overlay = Gtk.Overlay()
        overlay.add(outer)
        overlay.add_overlay(hbox)
        self.add(overlay)
        self.connect("draw", self._clear)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _clear(self, w, cr):
        cr.set_source_rgba(0,0,0,0)
        cr.set_operator(cairo.OPERATOR_SOURCE); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

    def _draw_bg(self, w, cr):
        ww = w.get_allocated_width()
        wh = w.get_allocated_height()
        rr(cr, 0, 0, ww, wh, 20)
        cr.set_source_rgba(*BG); cr.fill()
        rr(cr, 0.5, 0.5, ww-1, wh-1, 20)
        cr.set_source_rgba(1,1,1,0.07)
        cr.set_line_width(1); cr.stroke()


if __name__ == "__main__":
    widget = DesktopWidget()
    Gtk.main()
