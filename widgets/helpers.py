"""Cairo drawing helpers."""

import math
import cairo
from gi.repository import Gdk, GdkPixbuf
from widgets.config import CARD, BORDER


def rr(cr, x, y, w, h, r=12):
    """Rounded rectangle path."""
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


# ── Icon surface helpers ──

_icon_cache = {}


def _pb_to_surface(pb):
    w, h = pb.get_width(), pb.get_height()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
    cr.paint()
    return surf


def load_icon(name, size=48, direct_path=None):
    """Load an icon surface. Priority: direct_path > theme > filesystem."""
    import os
    from gi.repository import Gtk

    key = (name, size, direct_path)
    if key in _icon_cache:
        return _icon_cache[key]

    # 1. Direct path
    if direct_path and os.path.exists(direct_path):
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(direct_path, size, size, True)
            surf = _pb_to_surface(pb)
            _icon_cache[key] = surf
            return surf
        except Exception:
            pass

    # 2. GTK theme
    theme = Gtk.IconTheme.get_default()
    for c in [name, name.lower(), name.replace("-", "_"),
              name.replace("_", "-"), f"{name}-symbolic"]:
        try:
            pb = theme.load_icon(c, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if pb:
                surf = _pb_to_surface(pb)
                _icon_cache[key] = surf
                return surf
        except Exception:
            pass

    # 3. Filesystem search
    search = [
        f"/usr/share/icons/hicolor/{size}x{size}/apps/{name}.png",
        f"/usr/share/icons/hicolor/256x256/apps/{name}.png",
        f"/usr/share/icons/hicolor/scalable/apps/{name}.svg",
        f"/usr/share/pixmaps/{name}.png",
        f"/usr/share/pixmaps/{name}.xpm",
        f"/snap/{name}/current/meta/gui/icon.png",
    ]
    for p in search:
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


def blit_icon(cr, surf, cx, cy, size):
    if surf is None:
        return
    sw, sh = surf.get_width(), surf.get_height()
    scale = size / max(sw, sh)
    cr.save()
    cr.translate(cx - sw*scale/2, cy - sh*scale/2)
    cr.scale(scale, scale)
    cr.set_source_surface(surf, 0, 0)
    cr.paint()
    cr.restore()


def color_initial_icon(cr, cx, cy, r, letter, color):
    """Fallback: colored circle with initial letter."""
    from widgets.config import WHITE
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgba(*color[:3], 0.25)
    cr.fill()
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgba(*color[:3], 0.7)
    cr.set_line_width(1.5)
    cr.stroke()
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(r * 0.95)
    sc(cr, WHITE)
    e = cr.text_extents(letter)
    cr.move_to(cx - e.width/2, cy + e.height/2)
    cr.show_text(letter)
