"""Cairo vector icon drawing — no emoji, no theme dependency."""

import math


def draw_icon(cr, name, cx, cy, size, color):
    """Draw a vector icon centered at (cx, cy) with given size and color."""
    cr.save()
    cr.set_source_rgba(*color)
    cr.set_line_width(max(1.5, size * 0.08))
    cr.set_line_cap(1)  # ROUND
    cr.set_line_join(1)  # ROUND

    s = size / 2  # half-size for calculations
    fn = _ICONS.get(name)
    if fn:
        fn(cr, cx, cy, s, color)

    cr.restore()


def _power(cr, cx, cy, s, color):
    # Circle arc (open at top)
    cr.arc(cx, cy, s * 0.8, -1.2, math.pi + 1.2)
    cr.stroke()
    # Vertical line at top
    cr.move_to(cx, cy - s * 0.9)
    cr.line_to(cx, cy - s * 0.15)
    cr.stroke()


def _restart(cr, cx, cy, s, color):
    # Circular arrow
    cr.arc(cx, cy, s * 0.7, -0.5, math.pi * 1.5)
    cr.stroke()
    # Arrowhead
    ax = cx + s * 0.7 * math.cos(-0.5)
    ay = cy + s * 0.7 * math.sin(-0.5)
    cr.move_to(ax, ay)
    cr.line_to(ax + s * 0.3, ay - s * 0.1)
    cr.line_to(ax + s * 0.1, ay + s * 0.3)
    cr.close_path()
    cr.fill()


def _lock(cr, cx, cy, s, color):
    # Body (rounded rect)
    bw, bh = s * 1.2, s * 0.9
    bx, by = cx - bw/2, cy - bh/2 + s * 0.2
    cr.new_sub_path()
    r = s * 0.15
    cr.arc(bx + r, by + r, r, math.pi, 1.5*math.pi)
    cr.arc(bx + bw - r, by + r, r, 1.5*math.pi, 0)
    cr.arc(bx + bw - r, by + bh - r, r, 0, 0.5*math.pi)
    cr.arc(bx + r, by + bh - r, r, 0.5*math.pi, math.pi)
    cr.close_path()
    cr.fill()
    # Shackle (U-shape)
    cr.arc(cx, by, s * 0.35, math.pi, 0)
    cr.stroke()


def _logout(cr, cx, cy, s, color):
    # Arrow pointing right
    ax = cx + s * 0.2
    cr.move_to(ax - s * 0.4, cy)
    cr.line_to(ax + s * 0.5, cy)
    cr.stroke()
    # Arrowhead
    cr.move_to(ax + s * 0.5, cy)
    cr.line_to(ax + s * 0.15, cy - s * 0.35)
    cr.stroke()
    cr.move_to(ax + s * 0.5, cy)
    cr.line_to(ax + s * 0.15, cy + s * 0.35)
    cr.stroke()
    # Door frame (left bracket)
    cr.move_to(cx - s * 0.2, cy - s * 0.7)
    cr.line_to(cx - s * 0.6, cy - s * 0.7)
    cr.line_to(cx - s * 0.6, cy + s * 0.7)
    cr.line_to(cx - s * 0.2, cy + s * 0.7)
    cr.stroke()


def _moon(cr, cx, cy, s, color):
    # Crescent: large circle minus offset smaller circle
    r1 = s * 0.8
    r2 = s * 0.6
    off = s * 0.4
    cr.arc(cx, cy, r1, 0, 2 * math.pi)
    cr.close_path()
    cr.new_sub_path()
    cr.arc(cx + off, cy - off * 0.3, r2, 0, 2 * math.pi)
    cr.close_path()
    cr.set_fill_rule(0)  # EVEN_ODD
    cr.fill()
    cr.set_fill_rule(0)


def _speaker(cr, cx, cy, s, color):
    # Speaker cone
    cr.move_to(cx - s * 0.3, cy - s * 0.25)
    cr.line_to(cx - s * 0.3, cy + s * 0.25)
    cr.line_to(cx - s * 0.6, cy + s * 0.25)
    cr.line_to(cx - s * 0.6, cy - s * 0.25)
    cr.close_path()
    cr.fill()
    # Cone flare
    cr.move_to(cx - s * 0.3, cy - s * 0.25)
    cr.line_to(cx + s * 0.05, cy - s * 0.55)
    cr.line_to(cx + s * 0.05, cy + s * 0.55)
    cr.line_to(cx - s * 0.3, cy + s * 0.25)
    cr.close_path()
    cr.fill()
    # Sound waves
    for i, rs in enumerate([0.35, 0.55]):
        cr.arc(cx + s * 0.15, cy, s * rs, -0.6, 0.6)
        cr.stroke()


def _speaker_muted(cr, cx, cy, s, color):
    _speaker(cr, cx, cy, s, color)
    # Cross line
    cr.set_source_rgba(*color[:3], 0.9)
    cr.set_line_width(max(2, s * 0.12))
    cr.move_to(cx - s * 0.7, cy - s * 0.7)
    cr.line_to(cx + s * 0.7, cy + s * 0.7)
    cr.stroke()


def _wifi(cr, cx, cy, s, color):
    # Three arcs
    for r in [s * 0.35, s * 0.6, s * 0.85]:
        cr.arc(cx, cy + s * 0.3, r, -2.3, -0.84)
        cr.stroke()
    # Bottom dot
    cr.arc(cx, cy + s * 0.3, s * 0.1, 0, 2 * math.pi)
    cr.fill()


def _bluetooth(cr, cx, cy, s, color):
    # B shape
    top = cy - s * 0.8
    bot = cy + s * 0.8
    mid = cy
    cr.move_to(cx - s * 0.4, top + s * 0.35)
    cr.line_to(cx + s * 0.3, mid - s * 0.1)
    cr.line_to(cx, top)
    cr.line_to(cx, bot)
    cr.line_to(cx + s * 0.3, mid + s * 0.1)
    cr.line_to(cx - s * 0.4, bot - s * 0.35)
    cr.stroke()


def _play(cr, cx, cy, s, color):
    cr.move_to(cx - s * 0.4, cy - s * 0.6)
    cr.line_to(cx + s * 0.6, cy)
    cr.line_to(cx - s * 0.4, cy + s * 0.6)
    cr.close_path()
    cr.fill()


def _pause(cr, cx, cy, s, color):
    bw = s * 0.25
    gap = s * 0.15
    h = s * 0.7
    cr.rectangle(cx - gap - bw, cy - h, bw, h * 2)
    cr.fill()
    cr.rectangle(cx + gap, cy - h, bw, h * 2)
    cr.fill()


def _prev(cr, cx, cy, s, color):
    # Bar
    cr.rectangle(cx - s * 0.5, cy - s * 0.45, s * 0.15, s * 0.9)
    cr.fill()
    # Triangle pointing left
    cr.move_to(cx + s * 0.5, cy - s * 0.45)
    cr.line_to(cx - s * 0.25, cy)
    cr.line_to(cx + s * 0.5, cy + s * 0.45)
    cr.close_path()
    cr.fill()


def _next(cr, cx, cy, s, color):
    # Bar
    cr.rectangle(cx + s * 0.5 - s * 0.15, cy - s * 0.45, s * 0.15, s * 0.9)
    cr.fill()
    # Triangle pointing right
    cr.move_to(cx - s * 0.5, cy - s * 0.45)
    cr.line_to(cx + s * 0.25, cy)
    cr.line_to(cx - s * 0.5, cy + s * 0.45)
    cr.close_path()
    cr.fill()


def _search(cr, cx, cy, s, color):
    # Circle
    cr.arc(cx - s * 0.15, cy - s * 0.15, s * 0.5, 0, 2 * math.pi)
    cr.stroke()
    # Handle
    hx = cx - s * 0.15 + s * 0.5 * math.cos(math.pi * 0.25)
    hy = cy - s * 0.15 + s * 0.5 * math.sin(math.pi * 0.25)
    cr.move_to(hx, hy)
    cr.line_to(hx + s * 0.4, hy + s * 0.4)
    cr.stroke()


def _folder(cr, cx, cy, s, color):
    # Folder body
    bx, by = cx - s * 0.7, cy - s * 0.25
    bw, bh = s * 1.4, s * 0.85
    cr.new_sub_path()
    r = s * 0.1
    cr.arc(bx + r, by + r, r, math.pi, 1.5*math.pi)
    cr.arc(bx + bw - r, by + r, r, 1.5*math.pi, 0)
    cr.arc(bx + bw - r, by + bh - r, r, 0, 0.5*math.pi)
    cr.arc(bx + r, by + bh - r, r, 0.5*math.pi, math.pi)
    cr.close_path()
    cr.fill()
    # Tab
    tx = cx - s * 0.7
    ty = by - s * 0.2
    cr.move_to(tx, by)
    cr.line_to(tx, ty + s * 0.05)
    cr.line_to(tx + s * 0.5, ty + s * 0.05)
    cr.line_to(tx + s * 0.65, by)
    cr.close_path()
    cr.fill()


def _home(cr, cx, cy, s, color):
    # Roof
    cr.move_to(cx, cy - s * 0.75)
    cr.line_to(cx - s * 0.7, cy - s * 0.1)
    cr.line_to(cx + s * 0.7, cy - s * 0.1)
    cr.close_path()
    cr.fill()
    # House body
    cr.rectangle(cx - s * 0.5, cy - s * 0.1, s * 1.0, s * 0.7)
    cr.fill()
    # Door (cut-out)
    cr.set_source_rgba(0.10, 0.10, 0.13, 1)
    cr.rectangle(cx - s * 0.15, cy + s * 0.1, s * 0.3, s * 0.5)
    cr.fill()
    cr.set_source_rgba(*color)


def _downloads(cr, cx, cy, s, color):
    # Arrow pointing down
    cr.move_to(cx, cy - s * 0.6)
    cr.line_to(cx, cy + s * 0.15)
    cr.stroke()
    cr.move_to(cx - s * 0.35, cy - s * 0.15)
    cr.line_to(cx, cy + s * 0.25)
    cr.line_to(cx + s * 0.35, cy - s * 0.15)
    cr.stroke()
    # Tray
    cr.move_to(cx - s * 0.55, cy + s * 0.15)
    cr.line_to(cx - s * 0.55, cy + s * 0.55)
    cr.line_to(cx + s * 0.55, cy + s * 0.55)
    cr.line_to(cx + s * 0.55, cy + s * 0.15)
    cr.stroke()


_ICONS = {
    "power": _power,
    "restart": _restart,
    "lock": _lock,
    "logout": _logout,
    "moon": _moon,
    "speaker": _speaker,
    "speaker_muted": _speaker_muted,
    "wifi": _wifi,
    "bluetooth": _bluetooth,
    "play": _play,
    "pause": _pause,
    "prev": _prev,
    "next": _next,
    "search": _search,
    "folder": _folder,
    "home": _home,
    "downloads": _downloads,
}
