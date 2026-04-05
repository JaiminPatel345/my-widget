"""Center panel: Clock, Calendar, Music, Search."""

import math
import datetime
import calendar
import subprocess
import threading
import urllib.request
import cairo
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from widgets.config import CFG, CARD, CARD2, PINK, CYAN, WHITE, GREY, DIM, BORDER
from widgets.helpers import rr, draw_card, sc, _pb_to_surface
from widgets.icons import draw_icon


def _rr_clip(cr, x, y, w, h, r):
    """Rounded rect path (for clipping)."""
    import math as _m
    cr.new_sub_path()
    cr.arc(x + r, y + r, r, _m.pi, 1.5 * _m.pi)
    cr.arc(x + w - r, y + r, r, 1.5 * _m.pi, 0)
    cr.arc(x + w - r, y + h - r, r, 0, 0.5 * _m.pi)
    cr.arc(x + r, y + h - r, r, 0.5 * _m.pi, _m.pi)
    cr.close_path()


class CenterPanel(Gtk.DrawingArea):
    PW, PH = 430, 560

    def __init__(self):
        super().__init__()
        self.set_size_request(self.PW, self.PH)
        self._now = datetime.datetime.now()
        self._playing = False
        self._title = "YouTube"
        self._artist = "Open in Browser - Music"
        self._art_url = ""
        self._art_surf = None   # cached thumbnail surface
        self._progress = 0.0
        self._position = 0      # microseconds
        self._length = 0        # microseconds
        self._marquee = 0
        self._search = ""
        self._sfocus = False
        self._cursor_visible = True
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        self.set_can_focus(True)
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._on_click)
        self.connect("key-press-event", self._on_key)
        GLib.timeout_add(1000, self._clock_tick)
        GLib.timeout_add(50, self._anim_tick)
        GLib.timeout_add(1000, self._poll_player)
        GLib.timeout_add(500, self._blink_cursor)
        self._poll_player()

    def _clock_tick(self):
        self._now = datetime.datetime.now()
        self.queue_draw()
        return True

    def _anim_tick(self):
        if self._playing:
            self._marquee += 1
        self.queue_draw()
        return True

    def _blink_cursor(self):
        if self._sfocus:
            self._cursor_visible = not self._cursor_visible
            self.queue_draw()
        return True

    def _poll_player(self):
        def _do():
            try:
                s = subprocess.check_output(
                    ["playerctl", "status"],
                    stderr=subprocess.DEVNULL).decode().strip()
                self._playing = (s == "Playing")
                t = subprocess.check_output(
                    ["playerctl", "metadata", "title"],
                    stderr=subprocess.DEVNULL).decode().strip()
                a = subprocess.check_output(
                    ["playerctl", "metadata", "artist"],
                    stderr=subprocess.DEVNULL).decode().strip()
                art = subprocess.check_output(
                    ["playerctl", "metadata", "mpris:artUrl"],
                    stderr=subprocess.DEVNULL).decode().strip()
                # Get position (playerctl returns seconds as float)
                try:
                    pos_f = float(subprocess.check_output(
                        ["playerctl", "position"],
                        stderr=subprocess.DEVNULL).decode().strip())
                    self._position = int(pos_f * 1_000_000)
                except Exception:
                    self._position = 0
                # Get length (microseconds) from metadata
                try:
                    length = int(subprocess.check_output(
                        ["playerctl", "metadata", "mpris:length"],
                        stderr=subprocess.DEVNULL).decode().strip())
                    self._length = length
                except Exception:
                    self._length = 0
                # Compute progress
                if self._length > 0:
                    self._progress = min(1.0, self._position / self._length)
                else:
                    self._progress = 0.0
                self._title = t or "YouTube"
                self._artist = a or "Open in Browser - Music"
                if art != self._art_url:
                    self._art_url = art
                    self._load_art(art)
            except Exception:
                self._playing = False
                self._title = "YouTube"
                self._artist = "Open in Browser - Music"
                self._position = 0
                self._length = 0
                self._progress = 0.0
            GLib.idle_add(self.queue_draw)
        threading.Thread(target=_do, daemon=True).start()
        return True

    def _load_art(self, url):
        """Load album/video thumbnail into a cairo surface."""
        def _do():
            surf = None
            try:
                size = 250
                if url.startswith("file://"):
                    path = url[7:]
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
                    surf = _pb_to_surface(pb)
                elif url.startswith("http"):
                    tmp = "/tmp/_widget_art.jpg"
                    urllib.request.urlretrieve(url, tmp)
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp, size, size, True)
                    surf = _pb_to_surface(pb)
            except Exception:
                surf = None
            self._art_surf = surf
            GLib.idle_add(self.queue_draw)
        threading.Thread(target=_do, daemon=True).start()

    def _on_click(self, widget, event):
        self.grab_focus()
        x, y = event.x, event.y
        w, h = self.PW, self.PH
        pad = 14
        cw = w - pad * 2

        # Music controls
        mus_y = 210
        mus_h = h - 210 - 78
        ctl_y = mus_y + mus_h - pad - 14
        ctl_cx = w / 2

        if abs(y - ctl_y) < 22:
            if abs(x - (ctl_cx - 50)) < 20:
                subprocess.Popen(["playerctl", "previous"])
            elif abs(x - ctl_cx) < 20:
                subprocess.Popen(["playerctl", "play-pause"])
                self._playing = not self._playing
            elif abs(x - (ctl_cx + 50)) < 20:
                subprocess.Popen(["playerctl", "next"])
            self.queue_draw()
            return

        # Search bar click
        s_y = h - 68
        if s_y - 4 < y < h - 8:
            self._sfocus = True
            self._cursor_visible = True
            self.queue_draw()

    def _on_key(self, widget, event):
        if not self._sfocus:
            return
        k = event.keyval
        if k == Gdk.KEY_Return:
            q = self._search.strip()
            if q:
                subprocess.Popen(["xdg-open",
                                  f"https://google.com/search?q={q.replace(' ', '+')}"])
            self._search = ""
            self._sfocus = False
        elif k == Gdk.KEY_Escape:
            self._search = ""
            self._sfocus = False
        elif k == Gdk.KEY_BackSpace:
            self._search = self._search[:-1]
        else:
            ch = event.string
            if ch and ch.isprintable():
                self._search += ch
        self.queue_draw()

    def _draw(self, widget, cr):
        w, h = self.PW, self.PH
        pad = 14
        cw = w - pad * 2

        # ── TOP: Clock + Calendar ──
        clock_w = 180
        cal_w = cw - clock_w - 8
        top_h = 200

        draw_card(cr, pad, 0, clock_w, top_h, 14, CARD)
        self._draw_clock(cr, pad, 0, clock_w, top_h)

        draw_card(cr, pad + clock_w + 8, 0, cal_w, top_h, 14, CARD)
        self._draw_calendar(cr, pad + clock_w + 8, 0, cal_w, top_h)

        # ── MUSIC ──
        mus_y = top_h + 10
        mus_h = h - top_h - 10 - 78
        draw_card(cr, pad, mus_y, cw, mus_h, 14, CARD)
        self._draw_music(cr, pad, mus_y, cw, mus_h)

        # ── SEARCH ──
        s_y = h - 68
        s_h = 60
        draw_card(cr, pad, s_y, cw, s_h, 14, CARD2)
        self._draw_search(cr, pad, s_y, cw, s_h)

    def _draw_clock(self, cr, ox, oy, w, h):
        now = self._now
        cx = ox + w / 2

        cr.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(42)
        ts = now.strftime("%H:%M")
        te = cr.text_extents(ts)
        sc(cr, WHITE)
        cr.move_to(cx - te.width / 2, oy + 52)
        cr.show_text(ts)

        cr.set_font_size(14)
        sc(cr, PINK)
        ss = ":" + now.strftime("%S")
        cr.move_to(cx + te.width / 2 + 2, oy + 52)
        cr.show_text(ss)

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        sc(cr, GREY)
        ds = now.strftime("%A, %B %d")
        de = cr.text_extents(ds)
        cr.move_to(cx - de.width / 2, oy + 68)
        cr.show_text(ds)

        # Analog clock
        acx, acy, acr = cx, oy + h - 46, 38
        cr.arc(acx, acy, acr, 0, 2 * math.pi)
        cr.set_source_rgba(0.06, 0.06, 0.09, 1)
        cr.fill()
        cr.arc(acx, acy, acr, 0, 2 * math.pi)
        sc(cr, BORDER)
        cr.set_line_width(1)
        cr.stroke()

        for i in range(12):
            a = i * math.pi / 6 - math.pi / 2
            d = acr - 5
            cr.arc(acx + d * math.cos(a), acy + d * math.sin(a), 1.5, 0, 2 * math.pi)
            sc(cr, DIM)
            cr.fill()

        def hand(ang, length, lw, col):
            cr.set_line_width(lw)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            sc(cr, col)
            cr.move_to(acx, acy)
            cr.line_to(acx + length * math.cos(ang - math.pi / 2),
                       acy + length * math.sin(ang - math.pi / 2))
            cr.stroke()

        t = now
        hand((t.hour % 12 + t.minute / 60) * math.pi / 6, acr * 0.52, 2.5, WHITE)
        hand((t.minute + t.second / 60) * math.pi / 30, acr * 0.72, 1.8, GREY)
        hand(t.second * math.pi / 30, acr * 0.82, 1.2, PINK)
        cr.arc(acx, acy, 3, 0, 2 * math.pi)
        sc(cr, PINK)
        cr.fill()

    def _draw_calendar(self, cr, ox, oy, w, h):
        now = self._now
        pad = 10

        # Month header
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(14)
        sc(cr, CYAN)
        ms = now.strftime("%B %Y")
        me = cr.text_extents(ms)
        cr.move_to(ox + w / 2 - me.width / 2, oy + 22)
        cr.show_text(ms)

        # Day headers
        days_hdr = ["S", "M", "T", "W", "T", "F", "S"]
        cell = (w - pad * 2) / 7
        cr.set_font_size(10)
        hdr_y = oy + 40
        for i, d in enumerate(days_hdr):
            sc(cr, PINK if i in (0, 6) else DIM)
            de = cr.text_extents(d)
            cr.move_to(ox + pad + i * cell + cell / 2 - de.width / 2, hdr_y)
            cr.show_text(d)

        # Date grid — stretch rows to fill remaining height
        first_wd, num_days = calendar.monthrange(now.year, now.month)
        col = (first_wd + 1) % 7
        num_rows = math.ceil((((first_wd + 1) % 7) + num_days) / 7)
        grid_top = hdr_y + 10
        row_h = max(22, (h - (grid_top - oy) - 8) / num_rows)

        cr.set_font_size(11)
        row = 0
        for day in range(1, num_days + 1):
            dcx = ox + pad + col * cell + cell / 2
            dcy = grid_top + row * row_h + row_h / 2
            if day == now.day:
                cr.arc(dcx, dcy - 3, 10, 0, 2 * math.pi)
                sc(cr, CYAN)
                cr.fill()
                sc(cr, (0.07, 0.07, 0.09, 1))
            else:
                sc(cr, PINK if col in (0, 6) else GREY)
            de = cr.text_extents(str(day))
            cr.move_to(dcx - de.width / 2, dcy)
            cr.show_text(str(day))
            col += 1
            if col == 7:
                col = 0
                row += 1

    @staticmethod
    def _fmt_time(us):
        """Format microseconds as m:ss."""
        secs = max(0, int(us / 1_000_000))
        return f"{secs // 60}:{secs % 60:02d}"

    def _draw_music(self, cr, ox, oy, w, h):
        pad = 14
        inner_w = w - pad * 2

        # ── Top: Thumbnail (full width, ~55% height) ──
        thumb_h = int(h * 0.52)
        thumb_x = ox + pad
        thumb_y = oy + pad
        thumb_w = inner_w

        if self._art_surf:
            cr.save()
            _rr_clip(cr, thumb_x, thumb_y, thumb_w, thumb_h, 10)
            cr.clip()
            sw = self._art_surf.get_width()
            sh = self._art_surf.get_height()
            scale = max(thumb_w / sw, thumb_h / sh)
            cr.translate(thumb_x + (thumb_w - sw * scale) / 2,
                         thumb_y + (thumb_h - sh * scale) / 2)
            cr.scale(scale, scale)
            cr.set_source_surface(self._art_surf, 0, 0)
            cr.paint()
            cr.restore()
        else:
            rr(cr, thumb_x, thumb_y, thumb_w, thumb_h, 10)
            cr.set_source_rgba(*PINK[:3], 0.06)
            cr.fill()
            nx, ny = thumb_x + thumb_w / 2, thumb_y + thumb_h / 2
            sc(cr, DIM); cr.set_line_width(2)
            cr.arc(nx - 8, ny + 10, 7, 0, 2 * math.pi); cr.fill()
            cr.arc(nx + 8, ny + 6, 7, 0, 2 * math.pi); cr.fill()
            cr.set_source_rgba(*DIM[:3], 0.8)
            cr.move_to(nx - 1, ny + 10); cr.line_to(nx - 1, ny - 10)
            cr.line_to(nx + 15, ny - 14); cr.line_to(nx + 15, ny + 6)
            cr.stroke()

        # ── Bottom: Info + Progress + Controls ──
        bx = ox + pad
        by = thumb_y + thumb_h + 10
        bw = inner_w

        # Title
        title = self._title
        max_chars = max(16, int(bw / 8))
        if len(title) > max_chars:
            off = (self._marquee // 3) % (len(title) + 5)
            padded = title + "     "
            title = (padded * 2)[off:off + max_chars]

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(14)
        sc(cr, WHITE)
        cr.move_to(bx, by + 14)
        cr.show_text(title[:max_chars])

        # Artist
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10)
        sc(cr, GREY)
        cr.move_to(bx, by + 28)
        cr.show_text(self._artist[:max_chars])

        # Progress bar
        pb_y = by + 38
        pb_h = 3
        rr(cr, bx, pb_y, bw, pb_h, 2)
        cr.set_source_rgba(1, 1, 1, 0.08)
        cr.fill()
        if self._progress > 0:
            fill_w = max(4, bw * self._progress)
            rr(cr, bx, pb_y, fill_w, pb_h, 2)
            sc(cr, PINK)
            cr.fill()
            cr.arc(bx + fill_w, pb_y + pb_h / 2, 4, 0, 2 * math.pi)
            sc(cr, PINK); cr.fill()

        # Time labels
        cr.set_font_size(9)
        sc(cr, DIM)
        cr.move_to(bx, pb_y + 14)
        cr.show_text(self._fmt_time(self._position))
        len_str = self._fmt_time(self._length)
        le = cr.text_extents(len_str)
        cr.move_to(bx + bw - le.width, pb_y + 14)
        cr.show_text(len_str)

        # Controls — centered
        ctl_y = oy + h - pad - 14
        ctl_cx = ox + w / 2

        draw_icon(cr, "prev", ctl_cx - 50, ctl_y, 16, GREY)
        btn_sz = 30
        rr(cr, ctl_cx - btn_sz / 2, ctl_y - btn_sz / 2, btn_sz, btn_sz, 8)
        cr.set_source_rgba(*PINK[:3], 0.18); cr.fill()
        rr(cr, ctl_cx - btn_sz / 2, ctl_y - btn_sz / 2, btn_sz, btn_sz, 8)
        sc(cr, PINK); cr.set_line_width(1.2); cr.stroke()
        icon_name = "pause" if self._playing else "play"
        draw_icon(cr, icon_name, ctl_cx, ctl_y, 16, PINK)
        draw_icon(cr, "next", ctl_cx + 50, ctl_y, 16, GREY)

    def _draw_search(self, cr, ox, oy, w, h):
        pad = 14
        # Search icon (Cairo vector)
        draw_icon(cr, "search", ox + pad + 12, oy + h / 2, 18, GREY)

        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(13)
        if self._search:
            sc(cr, WHITE)
            disp = self._search[-32:]
            cr.move_to(ox + pad + 30, oy + h / 2 + 5)
            cr.show_text(disp)
            # Blinking cursor
            if self._sfocus and self._cursor_visible:
                te = cr.text_extents(disp)
                sc(cr, PINK)
                cr.set_line_width(1.5)
                cr.move_to(ox + pad + 30 + te.width + 2, oy + h / 2 - 8)
                cr.line_to(ox + pad + 30 + te.width + 2, oy + h / 2 + 8)
                cr.stroke()
        else:
            sc(cr, DIM)
            cr.move_to(ox + pad + 30, oy + h / 2 + 5)
            cr.show_text("Search the web...  (click here, then type)")
            # Blinking cursor at start
            if self._sfocus and self._cursor_visible:
                sc(cr, PINK)
                cr.set_line_width(1.5)
                cr.move_to(ox + pad + 30, oy + h / 2 - 8)
                cr.line_to(ox + pad + 30, oy + h / 2 + 8)
                cr.stroke()

        if self._sfocus:
            rr(cr, ox, oy, w, h, 14)
            sc(cr, PINK)
            cr.set_line_width(1.5)
            cr.stroke()
