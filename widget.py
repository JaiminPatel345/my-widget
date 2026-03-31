#!/usr/bin/env python3
"""Desktop Widget — 4-column layout: Profile/Weather | Clock/Music/Search | Apps/System | Files"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GLib
import cairo

from widgets.helpers import rr
from widgets.left_panel import LeftPanel
from widgets.center_panel import CenterPanel
from widgets.right_panel import RightPanel
from widgets.files_panel import FilesPanel

# Semi-transparent dark overlay alpha — compositor blurs the wallpaper behind this.
# Tune this value: lower = more wallpaper visible, higher = darker overlay.
_BG_ALPHA = 0.75


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

        # Make all GTK containers transparent so only Cairo draws the background
        css = Gtk.CssProvider()
        css.load_from_data(b"* { background: transparent; border: none; }")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        total_w = (LeftPanel.PW + 12 + CenterPanel.PW + 12 +
                   RightPanel.PW + 12 + FilesPanel.PW + 48)
        total_h = max(LeftPanel.PH, CenterPanel.PH,
                      RightPanel.PH, FilesPanel.PH) + 48
        self.set_default_size(total_w, total_h)

        sw, sh = screen.get_width(), screen.get_height()
        self.move((sw - total_w) // 2, (sh - total_h) // 2)

        # Background layer: draws the blurred/semi-transparent rounded rect
        bg = Gtk.DrawingArea()
        bg.set_size_request(total_w, total_h)
        bg.connect("draw", self._draw_bg)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(24)
        hbox.set_margin_bottom(24)
        hbox.set_margin_start(24)
        hbox.set_margin_end(24)
        hbox.pack_start(LeftPanel(), False, False, 0)
        hbox.pack_start(CenterPanel(), False, False, 0)
        hbox.pack_start(RightPanel(), False, False, 0)
        hbox.pack_start(FilesPanel(), False, False, 0)

        overlay = Gtk.Overlay()
        overlay.add(bg)
        overlay.add_overlay(hbox)
        self.add(overlay)

        self.connect("draw", self._clear)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _clear(self, w, cr):
        """Clear window to fully transparent so compositor can composite behind it."""
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

    def _draw_bg(self, w, cr):
        """Draw semi-transparent dark rounded rect.
        With picom blur-background=true this renders as blurred wallpaper + dark tint."""
        ww = w.get_allocated_width()
        wh = w.get_allocated_height()

        # Fully transparent base so the window shape is a rounded rect
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Dark blue-grey semi-transparent fill — compositor blurs wallpaper behind this
        rr(cr, 0, 0, ww, wh, 20)
        cr.set_source_rgba(0.12, 0.13, 0.17, _BG_ALPHA)
        cr.fill()

        # Subtle glassy border
        rr(cr, 0.5, 0.5, ww - 1, wh - 1, 20)
        cr.set_source_rgba(1, 1, 1, 0.08)
        cr.set_line_width(1)
        cr.stroke()


if __name__ == "__main__":
    widget = DesktopWidget()
    Gtk.main()
