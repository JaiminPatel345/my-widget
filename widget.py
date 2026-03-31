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

        # Force all GTK containers to be fully transparent
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

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(24)
        hbox.set_margin_bottom(24)
        hbox.set_margin_start(24)
        hbox.set_margin_end(24)
        hbox.pack_start(LeftPanel(), False, False, 0)
        hbox.pack_start(CenterPanel(), False, False, 0)
        hbox.pack_start(RightPanel(), False, False, 0)
        hbox.pack_start(FilesPanel(), False, False, 0)
        self.add(hbox)
        self.connect("draw", self._clear)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _clear(self, w, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)


if __name__ == "__main__":
    widget = DesktopWidget()
    Gtk.main()
