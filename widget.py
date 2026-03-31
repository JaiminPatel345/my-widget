#!/usr/bin/env python3
"""
Desktop Widget — GTK3 + Cairo glassmorphism desktop widget for Ubuntu.
Sections: Clock/Calendar · Profile/Weather · Music · App Launcher · Quick Toggles
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
import cairo
import subprocess
import threading
import datetime
import math
import os
import sys

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
USERNAME = os.environ.get("USER") or os.environ.get("LOGNAME") or "User"
PROFILE_IMAGE_PATH = os.path.expanduser("~/Pictures/profile.jpg")
CITY = "auto"          # set to e.g. "London" for a specific city

# Color helpers (RGBA 0‥1)
BG_DARK        = (0.039, 0.039, 0.059, 0.92)   # #0a0a0f  semi-transparent
GLASS_CARD     = (1.0,   1.0,   1.0,   0.07)
ACCENT         = (0.0,   0.831, 1.0,   1.0)    # #00d4ff
ACCENT_DIM     = (0.0,   0.831, 1.0,   0.25)
TEXT_PRIMARY   = (1.0,   1.0,   1.0,   0.95)
TEXT_SECONDARY = (1.0,   1.0,   1.0,   0.55)
GLOW_BORDER    = (0.0,   0.831, 1.0,   0.35)

WIDGET_WIDTH  = 420
SECTION_PAD   = 16
CORNER_RADIUS = 18

# ─────────────────────────────────────────────
# UTILITY — rounded rectangle path
# ─────────────────────────────────────────────

def rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + r,     y + r,     r, math.pi,       1.5 * math.pi)
    ctx.arc(x + w - r, y + r,     r, 1.5 * math.pi, 0)
    ctx.arc(x + w - r, y + h - r, r, 0,              0.5 * math.pi)
    ctx.arc(x + r,     y + h - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()


def draw_glass_card(ctx, x, y, w, h, r=CORNER_RADIUS):
    """Draw a semi-transparent glass card with a subtle border glow."""
    # Background fill
    ctx.save()
    rounded_rect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*GLASS_CARD)
    ctx.fill_preserve()
    # Border glow
    ctx.set_source_rgba(*GLOW_BORDER)
    ctx.set_line_width(1.2)
    ctx.stroke()
    ctx.restore()


def set_color(ctx, rgba):
    ctx.set_source_rgba(*rgba)


def pango_layout(widget, ctx, text, size_pts, bold=False, mono=False):
    layout = PangoCairo.create_layout(ctx)
    family = "JetBrains Mono" if mono else "Outfit"
    weight = "Bold" if bold else "Regular"
    layout.set_font_description(
        Pango.font_description_from_string(f"{family} {weight} {size_pts}")
    )
    layout.set_text(text, -1)
    return layout


# ─────────────────────────────────────────────
# BACKGROUND AURORA ANIMATION
# ─────────────────────────────────────────────

class AuroraBackground:
    def __init__(self):
        self.phase = 0.0

    def tick(self):
        self.phase += 0.008

    def draw(self, ctx, w, h):
        # Dark base
        ctx.set_source_rgba(*BG_DARK)
        ctx.paint()

        # Soft aurora blobs
        blobs = [
            (0.3 + 0.15 * math.sin(self.phase),
             0.25 + 0.1  * math.cos(self.phase * 0.7),
             0.35, (0.0, 0.4, 0.8, 0.06)),
            (0.7 + 0.1  * math.cos(self.phase * 0.9),
             0.6 + 0.15  * math.sin(self.phase * 1.1),
             0.30, (0.0, 0.6, 0.4, 0.05)),
            (0.5 + 0.1  * math.sin(self.phase * 1.3),
             0.8 + 0.05  * math.cos(self.phase * 0.6),
             0.25, (0.4, 0.0, 0.8, 0.04)),
        ]
        for bx, by, br, color in blobs:
            grd = cairo.RadialGradient(
                bx * w, by * h, 0,
                bx * w, by * h, br * max(w, h)
            )
            grd.add_color_stop_rgba(0,   *color)
            grd.add_color_stop_rgba(1,   color[0], color[1], color[2], 0)
            ctx.set_source(grd)
            ctx.paint()


# ─────────────────────────────────────────────
# SECTION: CLOCK + CALENDAR
# ─────────────────────────────────────────────

class ClockSection:
    DAYS   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    MONTHS = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

    def get_height(self):
        return 230

    def draw(self, ctx, widget, x, y, w):
        h = self.get_height()
        draw_glass_card(ctx, x, y, w, h)

        now = datetime.datetime.now()

        # ── Clock digits ──────────────────────────────────
        time_str = now.strftime("%H:%M:%S")
        layout = pango_layout(widget, ctx, time_str, 48, bold=True, mono=True)
        pw, ph = layout.get_pixel_size()
        ctx.save()
        ctx.translate(x + (w - pw) / 2, y + 18)
        set_color(ctx, ACCENT)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        # ── Date ──────────────────────────────────────────
        day_name = self.DAYS[now.weekday()]
        month    = self.MONTHS[now.month - 1]
        date_str = f"{day_name}, {month} {now.day}"
        layout = pango_layout(widget, ctx, date_str, 13, bold=False)
        pw, ph = layout.get_pixel_size()
        ctx.save()
        ctx.translate(x + (w - pw) / 2, y + 76)
        set_color(ctx, TEXT_SECONDARY)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        # ── Mini calendar ──────────────────────────────────
        self._draw_calendar(ctx, widget, x + SECTION_PAD, y + 100, w - 2*SECTION_PAD, now)

    def _draw_calendar(self, ctx, widget, cx, cy, cw, now):
        import calendar
        cell_w = cw / 7
        cell_h = 18

        day_letters = ["Mo","Tu","We","Th","Fr","Sa","Su"]
        for i, d in enumerate(day_letters):
            layout = pango_layout(widget, ctx, d, 8)
            pw, _ = layout.get_pixel_size()
            ctx.save()
            ctx.translate(cx + i * cell_w + (cell_w - pw) / 2, cy)
            set_color(ctx, TEXT_SECONDARY)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()

        cal = calendar.monthcalendar(now.year, now.month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                tx = cx + col_idx * cell_w
                ty = cy + (row_idx + 1) * cell_h + 4
                is_today = (day == now.day)

                if is_today:
                    # Cyan highlight circle
                    ctx.save()
                    ctx.arc(tx + cell_w / 2, ty + cell_h / 2 - 1, cell_h / 2 - 1, 0, 2*math.pi)
                    set_color(ctx, ACCENT_DIM)
                    ctx.fill()
                    ctx.restore()

                layout = pango_layout(widget, ctx, str(day), 9, bold=is_today)
                pw, ph = layout.get_pixel_size()
                ctx.save()
                ctx.translate(tx + (cell_w - pw) / 2, ty + (cell_h - ph) / 2 - 1)
                set_color(ctx, ACCENT if is_today else TEXT_PRIMARY)
                PangoCairo.show_layout(ctx, layout)
                ctx.restore()


# ─────────────────────────────────────────────
# SECTION: PROFILE + WEATHER
# ─────────────────────────────────────────────

class ProfileSection:
    def __init__(self):
        self.weather_text  = "Fetching…"
        self.weather_icon  = "🌡"
        self.uptime_text   = ""
        self._pixbuf       = None
        self._load_avatar()
        self._fetch_weather_async()
        GLib.timeout_add(1_800_000, self._fetch_weather_async)  # refresh every 30 min (1,800,000 ms)

    def _load_avatar(self):
        from gi.repository import GdkPixbuf
        size = 70
        if os.path.exists(PROFILE_IMAGE_PATH):
            try:
                self._pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    PROFILE_IMAGE_PATH, size, size, True)
                return
            except Exception:
                pass
        # Fallback: None → draw placeholder
        self._pixbuf = None

    def _fetch_weather_async(self):
        def _fetch():
            if not HAS_REQUESTS:
                GLib.idle_add(self._set_weather, "requests not installed", "⚠")
                return
            try:
                url  = f"https://wttr.in/{CITY}?format=j1"
                resp = requests.get(url, timeout=8)
                data = resp.json()
                cur  = data["current_condition"][0]
                temp = cur["temp_C"]
                desc = cur["weatherDesc"][0]["value"]
                code = int(cur["weatherCode"])
                icon = self._weather_icon(code)
                GLib.idle_add(self._set_weather, f"{temp}°C  {desc}", icon)
            except Exception:
                GLib.idle_add(self._set_weather, "Weather unavailable", "🌫")
        threading.Thread(target=_fetch, daemon=True).start()
        return True  # keep GLib timer alive

    def _set_weather(self, text, icon):
        self.weather_text = text
        self.weather_icon = icon

    @staticmethod
    def _weather_icon(code):
        if code in (113,):            return "☀"
        if code in (116, 119):        return "⛅"
        if code in (122, 143):        return "☁"
        if code in (176, 185, 293, 296, 299, 302, 305, 308): return "🌧"
        if code in (200, 386, 389):   return "⛈"
        if code in (179, 182, 227, 230, 323, 326, 329, 332, 335, 338, 350, 362, 365, 371, 374, 377): return "❄"
        return "🌡"

    def _get_uptime(self):
        try:
            with open("/proc/uptime") as f:
                secs = float(f.read().split()[0])
            h = int(secs // 3600)
            m = int((secs % 3600) // 60)
            return f"Up {h}h {m}m"
        except Exception:
            return ""

    def get_height(self):
        return 120

    def draw(self, ctx, widget, x, y, w):
        h = self.get_height()
        draw_glass_card(ctx, x, y, w, h)

        AV = 70   # avatar size
        av_x = x + SECTION_PAD
        av_y = y + (h - AV) // 2

        # ── Avatar circle ──────────────────────────────────
        ctx.save()
        ctx.arc(av_x + AV/2, av_y + AV/2, AV/2, 0, 2*math.pi)
        ctx.clip()
        if self._pixbuf:
            Gdk.cairo_set_source_pixbuf(ctx, self._pixbuf, av_x, av_y)
            ctx.paint()
        else:
            # Placeholder gradient
            grd = cairo.RadialGradient(av_x + AV/2, av_y + AV/2, 0,
                                       av_x + AV/2, av_y + AV/2, AV/2)
            grd.add_color_stop_rgba(0, 0.0, 0.5, 0.7, 1)
            grd.add_color_stop_rgba(1, 0.0, 0.2, 0.4, 1)
            ctx.set_source(grd)
            ctx.paint()
            # Person silhouette
            ctx.set_source_rgba(1, 1, 1, 0.5)
            ctx.arc(av_x + AV/2, av_y + AV*0.35, AV*0.18, 0, 2*math.pi)
            ctx.fill()
            ctx.arc(av_x + AV/2, av_y + AV*0.80, AV*0.28, math.pi, 0)
            ctx.fill()
        ctx.restore()

        # Cyan ring around avatar
        ctx.arc(av_x + AV/2, av_y + AV/2, AV/2 + 1.5, 0, 2*math.pi)
        set_color(ctx, ACCENT)
        ctx.set_line_width(1.5)
        ctx.stroke()

        text_x = av_x + AV + 14
        # ── Username ──────────────────────────────────────
        layout = pango_layout(widget, ctx, USERNAME, 15, bold=True)
        ctx.save()
        ctx.translate(text_x, y + 20)
        set_color(ctx, TEXT_PRIMARY)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        # ── Weather ───────────────────────────────────────
        weather_line = f"{self.weather_icon}  {self.weather_text}"
        layout = pango_layout(widget, ctx, weather_line, 10)
        ctx.save()
        ctx.translate(text_x, y + 44)
        set_color(ctx, TEXT_SECONDARY)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        # ── Uptime badge ──────────────────────────────────
        uptime = self._get_uptime()
        if uptime:
            layout = pango_layout(widget, ctx, uptime, 8)
            pw, ph = layout.get_pixel_size()
            bx = text_x
            by = y + 68
            draw_glass_card(ctx, bx - 4, by - 2, pw + 10, ph + 4, r=6)
            ctx.save()
            ctx.translate(bx + 1, by)
            set_color(ctx, ACCENT)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()


# ─────────────────────────────────────────────
# SECTION: MUSIC CONTROL
# ─────────────────────────────────────────────

class MusicSection:
    def __init__(self, widget_ref):
        self.widget_ref   = widget_ref
        self.title        = "Nothing playing"
        self.artist       = ""
        self.playing      = False
        self.disc_angle   = 0.0
        self.scroll_off   = 0
        self._album_pixbuf = None
        self._fetch()
        GLib.timeout_add(3000, self._fetch)

    def _run(self, *args):
        try:
            return subprocess.check_output(
                ["playerctl"] + list(args),
                stderr=subprocess.DEVNULL, text=True
            ).strip()
        except Exception:
            return ""

    def _fetch(self):
        def _do():
            status = self._run("status")
            title  = self._run("metadata", "title")
            artist = self._run("metadata", "artist")
            if not title:
                title  = "Browser Audio"
                artist = ""
                status = ""
            GLib.idle_add(self._update, title, artist, status == "Playing")
        threading.Thread(target=_do, daemon=True).start()
        return True

    def _update(self, title, artist, playing):
        self.title   = title
        self.artist  = artist
        self.playing = playing

    def tick_spin(self):
        if self.playing:
            self.disc_angle += 0.04
            if self.disc_angle > 2 * math.pi:
                self.disc_angle -= 2 * math.pi
        # Scrolling marquee
        self.scroll_off = (self.scroll_off + 1) % 200

    def cmd(self, action):
        subprocess.Popen(["playerctl", action],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_height(self):
        return 160

    def draw(self, ctx, widget, x, y, w):
        h = self.get_height()
        draw_glass_card(ctx, x, y, w, h)

        DISC = 80
        dx   = x + SECTION_PAD + DISC // 2
        dy   = y + h // 2

        # ── Spinning disc ─────────────────────────────────
        ctx.save()
        ctx.translate(dx, dy)
        ctx.rotate(self.disc_angle)

        # Outer ring gradient
        grd = cairo.RadialGradient(0, 0, 0, 0, 0, DISC/2)
        grd.add_color_stop_rgba(0,   0.05, 0.05, 0.1, 1)
        grd.add_color_stop_rgba(0.35, 0.0, 0.3,  0.5, 1)
        grd.add_color_stop_rgba(0.7,  0.0, 0.15, 0.3, 1)
        grd.add_color_stop_rgba(1,    0.0, 0.5,  0.7, 1)
        ctx.arc(0, 0, DISC/2, 0, 2*math.pi)
        ctx.set_source(grd)
        ctx.fill()

        # Vinyl grooves
        ctx.set_line_width(0.5)
        set_color(ctx, (1, 1, 1, 0.07))
        for r in range(int(DISC*0.15), int(DISC*0.48), 4):
            ctx.arc(0, 0, r, 0, 2*math.pi)
            ctx.stroke()

        # Centre hole
        ctx.arc(0, 0, DISC*0.08, 0, 2*math.pi)
        set_color(ctx, (0.0, 0.831, 1.0, 1.0))
        ctx.fill()
        ctx.arc(0, 0, DISC*0.03, 0, 2*math.pi)
        set_color(ctx, (0.05, 0.05, 0.1, 1))
        ctx.fill()

        ctx.restore()

        # Glow ring
        ctx.arc(dx, dy, DISC/2 + 2, 0, 2*math.pi)
        set_color(ctx, GLOW_BORDER if self.playing else (1, 1, 1, 0.1))
        ctx.set_line_width(1.5)
        ctx.stroke()

        # ── Text ──────────────────────────────────────────
        tx = x + SECTION_PAD + DISC + 14
        tw = w - tx + x - SECTION_PAD

        # Scrolling title
        title_full = self.title or "Nothing playing"
        layout = pango_layout(widget, ctx, title_full, 12, bold=True)
        pw, ph = layout.get_pixel_size()
        ctx.save()
        ctx.rectangle(tx, y + 28, tw, ph + 2)
        ctx.clip()
        scroll_px = (self.scroll_off * 1) % max(pw + 40, 1) if pw > tw else 0
        ctx.translate(tx - scroll_px, y + 28)
        set_color(ctx, TEXT_PRIMARY)
        PangoCairo.show_layout(ctx, layout)
        if pw > tw:
            ctx.translate(pw + 40, 0)
            PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        if self.artist:
            layout = pango_layout(widget, ctx, self.artist, 10)
            ctx.save()
            ctx.translate(tx, y + 50)
            set_color(ctx, TEXT_SECONDARY)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()

        # ── Controls ──────────────────────────────────────
        buttons = [("⏮", "previous"), ("⏸" if self.playing else "▶", "play-pause"), ("⏭", "next")]
        bw  = 36
        gap = 10
        total = len(buttons) * bw + (len(buttons)-1) * gap
        bx_start = tx
        by = y + h - bw - 14

        for i, (icon, action) in enumerate(buttons):
            bx = bx_start + i * (bw + gap)
            rounded_rect(ctx, bx, by, bw, bw, 8)
            set_color(ctx, GLASS_CARD)
            ctx.fill_preserve()
            set_color(ctx, GLOW_BORDER)
            ctx.set_line_width(1)
            ctx.stroke()

            layout = pango_layout(widget, ctx, icon, 16)
            iw, ih = layout.get_pixel_size()
            ctx.save()
            ctx.translate(bx + (bw - iw) / 2, by + (bw - ih) / 2)
            set_color(ctx, ACCENT)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()


# ─────────────────────────────────────────────
# SECTION: APP LAUNCHER
# ─────────────────────────────────────────────

class AppLauncherSection:
    APPS = [
        ("Chrome",      "google-chrome",    "google-chrome"),
        ("Brave",       "brave-browser",    "brave-browser"),
        ("Discord",     "discord",          "discord"),
        ("YouTube",     "🎬",               "xdg-open https://youtube.com"),
        ("Calculator",  "gnome-calculator", "gnome-calculator"),
        ("Files",       "nautilus",         "nautilus"),
    ]

    def __init__(self):
        self.hover_idx     = -1
        self.hover_scale   = {}
        self._icon_pixbufs = {}
        self._load_icons()

    def _load_icons(self):
        from gi.repository import GdkPixbuf
        icon_theme = Gtk.IconTheme.get_default()
        for name, icon_id, _ in self.APPS:
            if icon_id.startswith("🎬"):
                self._icon_pixbufs[name] = None
                continue
            try:
                pb = icon_theme.load_icon(icon_id, 40, 0)
                self._icon_pixbufs[name] = pb
            except Exception:
                self._icon_pixbufs[name] = None

    def launch(self, idx):
        _, _, cmd = self.APPS[idx]
        subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_height(self):
        return 130

    def draw(self, ctx, widget, x, y, w):
        h = self.get_height()
        draw_glass_card(ctx, x, y, w, h)

        n     = len(self.APPS)
        cols  = 6
        rows  = math.ceil(n / cols)
        cell_w = (w - 2*SECTION_PAD) / cols
        cell_h = (h - 2*SECTION_PAD - 16) / rows

        layout = pango_layout(widget, ctx, "APP LAUNCHER", 8)
        ctx.save()
        ctx.translate(x + SECTION_PAD, y + 6)
        set_color(ctx, TEXT_SECONDARY)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        for i, (name, icon_id, _) in enumerate(self.APPS):
            col = i % cols
            row = i // cols
            cx  = x + SECTION_PAD + col * cell_w
            cy  = y + 22 + row * cell_h
            scale = self.hover_scale.get(i, 1.0)

            # Hover glow background
            if scale > 1.01:
                rounded_rect(ctx, cx + 2, cy + 2, cell_w - 4, cell_h - 4, 8)
                set_color(ctx, ACCENT_DIM)
                ctx.fill()

            ICON = 28
            ix   = cx + (cell_w - ICON) / 2
            iy   = cy + 4

            pb = self._icon_pixbufs.get(name)
            if pb:
                ctx.save()
                ctx.translate(ix + ICON/2, iy + ICON/2)
                ctx.scale(scale, scale)
                ctx.translate(-ICON/2, -ICON/2)
                Gdk.cairo_set_source_pixbuf(ctx, pb, 0, 0)
                ctx.paint()
                ctx.restore()
            else:
                # Emoji fallback
                layout2 = pango_layout(widget, ctx, icon_id, 20)
                pw, ph = layout2.get_pixel_size()
                ctx.save()
                ctx.translate(cx + (cell_w - pw) / 2, iy)
                ctx.scale(scale, scale)
                set_color(ctx, ACCENT)
                PangoCairo.show_layout(ctx, layout2)
                ctx.restore()

            # Label
            layout2 = pango_layout(widget, ctx, name, 7)
            pw, _ = layout2.get_pixel_size()
            ctx.save()
            ctx.translate(cx + (cell_w - pw) / 2, iy + ICON + 2)
            set_color(ctx, TEXT_SECONDARY)
            PangoCairo.show_layout(ctx, layout2)
            ctx.restore()

    def icon_rect(self, idx, widget_x, widget_y, w):
        cols  = 6
        cell_w = (w - 2*SECTION_PAD) / cols
        cell_h = (130 - 2*SECTION_PAD - 16) / math.ceil(len(self.APPS) / cols)
        col = idx % cols
        row = idx // cols
        return (widget_x + SECTION_PAD + col * cell_w,
                widget_y + 22 + row * cell_h,
                cell_w, cell_h)


# ─────────────────────────────────────────────
# SECTION: QUICK TOGGLES
# ─────────────────────────────────────────────

class QuickTogglesSection:
    TOGGLES = ["WiFi", "BT", "Night", "Power"]

    def __init__(self):
        self.states = {"WiFi": False, "BT": False, "Night": False, "Power": False}
        self._detect_states()

    def _detect_states(self):
        def _do():
            wifi_on = False
            bt_on   = False
            try:
                out = subprocess.check_output(
                    ["nmcli", "radio", "wifi"], text=True, stderr=subprocess.DEVNULL
                ).strip()
                wifi_on = out.lower() == "enabled"
            except Exception:
                pass
            try:
                out = subprocess.check_output(
                    ["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL
                )
                bt_on = "Powered: yes" in out
            except Exception:
                pass
            GLib.idle_add(self._apply_states, wifi_on, bt_on)
        threading.Thread(target=_do, daemon=True).start()

    def _apply_states(self, wifi, bt):
        self.states["WiFi"] = wifi
        self.states["BT"]   = bt

    def toggle(self, name):
        if name == "WiFi":
            new = not self.states["WiFi"]
            cmd = ["nmcli", "radio", "wifi", "on" if new else "off"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.states["WiFi"] = new
        elif name == "BT":
            new = not self.states["BT"]
            cmd = ["bluetoothctl", "power", "on" if new else "off"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.states["BT"] = new
        elif name == "Night":
            new = not self.states["Night"]
            if new:
                subprocess.Popen(["redshift", "-O", "3500"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["redshift", "-x"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.states["Night"] = new
        elif name == "Power":
            self._show_power_menu()

    def _show_power_menu(self):
        dialog = Gtk.Dialog(title="Power", flags=0)
        dialog.set_decorated(True)
        dialog.add_buttons(
            "Shutdown", 1,
            "Restart",  2,
            "Logout",   3,
            "Cancel",   0,
        )
        dialog.get_content_area().add(
            Gtk.Label(label="Choose a power action:")
        )
        dialog.show_all()
        resp = dialog.run()
        dialog.destroy()
        if resp == 1:
            subprocess.Popen(["systemctl", "poweroff"])
        elif resp == 2:
            subprocess.Popen(["systemctl", "reboot"])
        elif resp == 3:
            subprocess.Popen(["gnome-session-quit", "--logout", "--no-prompt"])

    ICONS = {"WiFi": "📶", "BT": "🔵", "Night": "🌙", "Power": "⏻"}

    def get_height(self):
        return 74

    def draw(self, ctx, widget, x, y, w):
        h = self.get_height()
        draw_glass_card(ctx, x, y, w, h)

        layout = pango_layout(widget, ctx, "QUICK TOGGLES", 8)
        ctx.save()
        ctx.translate(x + SECTION_PAD, y + 6)
        set_color(ctx, TEXT_SECONDARY)
        PangoCairo.show_layout(ctx, layout)
        ctx.restore()

        n    = len(self.TOGGLES)
        pw   = (w - 2*SECTION_PAD - (n-1)*8) / n
        ph   = 36
        py_  = y + 24

        for i, name in enumerate(self.TOGGLES):
            bx = x + SECTION_PAD + i * (pw + 8)
            on = self.states.get(name, False)

            # Pill background
            rounded_rect(ctx, bx, py_, pw, ph, ph/2)
            if on:
                set_color(ctx, (0.0, 0.4, 0.55, 0.5))
            else:
                set_color(ctx, (1, 1, 1, 0.06))
            ctx.fill_preserve()
            set_color(ctx, ACCENT if on else (1, 1, 1, 0.15))
            ctx.set_line_width(1.2)
            ctx.stroke()

            icon  = self.ICONS[name]
            label = f"{icon} {name}"
            layout2 = pango_layout(widget, ctx, label, 9, bold=on)
            lw, lh = layout2.get_pixel_size()
            ctx.save()
            ctx.translate(bx + (pw - lw) / 2, py_ + (ph - lh) / 2)
            set_color(ctx, ACCENT if on else TEXT_SECONDARY)
            PangoCairo.show_layout(ctx, layout2)
            ctx.restore()

    def button_rects(self, x, y, w):
        n    = len(self.TOGGLES)
        pw   = (w - 2*SECTION_PAD - (n-1)*8) / n
        ph   = 36
        py_  = y + 24
        rects = []
        for i in range(n):
            bx = x + SECTION_PAD + i * (pw + 8)
            rects.append((bx, py_, pw, ph))
        return rects


# ─────────────────────────────────────────────
# MAIN WIDGET WINDOW
# ─────────────────────────────────────────────

class DesktopWidget(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # ── Window properties ─────────────────────────────
        self.set_title("desktop-widget")
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_accept_focus(False)
        self.stick()  # show on all workspaces

        # ── RGBA / transparency ───────────────────────────
        screen  = self.get_screen()
        visual  = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        # ── Size & position ───────────────────────────────
        self.set_default_size(WIDGET_WIDTH, 10)
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        self.move((screen_w - WIDGET_WIDTH) // 2, (screen_h - 720) // 2)

        # ── Sections ──────────────────────────────────────
        self.aurora   = AuroraBackground()
        self.clock_s  = ClockSection()
        self.profile  = ProfileSection()
        self.music    = MusicSection(self)
        self.apps     = AppLauncherSection()
        self.toggles  = QuickTogglesSection()

        # Sections list with y offsets (computed on draw)
        self._section_layout = []

        # ── Drawing area ──────────────────────────────────
        self.da = Gtk.DrawingArea()
        self.da.connect("draw", self._on_draw)
        self.da.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.da.connect("button-press-event", self._on_click)
        self.da.connect("motion-notify-event", self._on_motion)

        # Scrolled window for small screens
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.da)
        self.add(sw)

        # ── Timers ────────────────────────────────────────
        GLib.timeout_add(1000, self._tick_clock)
        GLib.timeout_add(50,   self._tick_spin)
        GLib.timeout_add(30_000, self._tick_aurora)   # aurora tick every 30 seconds

        self.show_all()

    # ── Timer callbacks ───────────────────────────────────

    def _tick_clock(self):
        self.da.queue_draw()
        return True

    def _tick_spin(self):
        self.music.tick_spin()
        self.da.queue_draw()
        return True

    def _tick_aurora(self):
        self.aurora.tick()
        return True

    # ── Draw ──────────────────────────────────────────────

    def _on_draw(self, widget, ctx):
        alloc = widget.get_allocation()
        W, H  = alloc.width, alloc.height

        # Transparent base
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)

        # Aurora background
        self.aurora.draw(ctx, W, H)

        # Sections
        sections = [
            ("clock",   self.clock_s),
            ("profile", self.profile),
            ("music",   self.music),
            ("apps",    self.apps),
            ("toggles", self.toggles),
        ]
        GAP = 12
        pad = SECTION_PAD
        x   = pad
        y   = pad
        w   = W - 2 * pad

        self._section_layout = []
        for key, sec in sections:
            h = sec.get_height()
            sec.draw(ctx, widget, x, y, w)
            self._section_layout.append((key, sec, x, y, w, h))
            y += h + GAP

        # Resize drawing area to fit content
        total_h = y + pad
        if self.da.get_allocated_height() < total_h - 10:
            self.da.set_size_request(W, total_h)

    # ── Input handling ────────────────────────────────────

    def _on_click(self, widget, event):
        ex, ey = event.x, event.y
        for key, sec, sx, sy, sw, sh in self._section_layout:
            if key == "music":
                # Check control buttons
                buttons = [("previous",), ("play-pause",), ("next",)]
                DISC = 80
                tx = sx + SECTION_PAD + DISC + 14
                bw = 36; gap = 10
                by = sy + sh - bw - 14
                for i, (action,) in enumerate(buttons):
                    bx = tx + i * (bw + gap)
                    if bx <= ex <= bx + bw and by <= ey <= by + bw:
                        self.music.cmd(action)
                        return

            elif key == "apps":
                for i in range(len(self.apps.APPS)):
                    rx, ry, rw, rh = self.apps.icon_rect(i, sx, sy, sw)
                    if rx <= ex <= rx + rw and ry <= ey <= ry + rh:
                        self.apps.launch(i)
                        return

            elif key == "toggles":
                rects = self.toggles.button_rects(sx, sy, sw)
                for i, (bx, by, bw, bh) in enumerate(rects):
                    if bx <= ex <= bx + bw and by <= ey <= by + bh:
                        self.toggles.toggle(self.toggles.TOGGLES[i])
                        self.da.queue_draw()
                        return

    def _on_motion(self, widget, event):
        ex, ey = event.x, event.y
        changed = False
        for key, sec, sx, sy, sw, sh in self._section_layout:
            if key != "apps":
                continue
            for i in range(len(self.apps.APPS)):
                rx, ry, rw, rh = self.apps.icon_rect(i, sx, sy, sw)
                inside = rx <= ex <= rx + rw and ry <= ey <= ry + rh
                target = 1.15 if inside else 1.0
                prev   = self.apps.hover_scale.get(i, 1.0)
                # Smooth approach
                new    = prev + (target - prev) * 0.25
                if abs(new - prev) > 0.002:
                    self.apps.hover_scale[i] = new
                    changed = True
                else:
                    self.apps.hover_scale[i] = target
        if changed:
            self.da.queue_draw()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    widget = DesktopWidget()
    widget.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
