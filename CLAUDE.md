# my-widget — Claude Instructions

## Project Overview
GTK3 desktop widget for Ubuntu using Cairo for custom drawing. Python 3, no Qt.

## Architecture
```
widget.py          # entry point
config.json        # ALL user config (name, apps, files, toggles)
widgets/
  config.py        # load config.json
  helpers.py       # cairo utilities: rr(), draw_card(), sc(), blit_icon()
  icons.py         # icon loading + Cairo vector icon drawing functions
  left_panel.py    # profile, weather, quote
  center_panel.py  # clock, calendar, music, search
  right_panel.py   # app launcher + unified system panel (toggles + actions)
  files_panel.py   # file system quick-links
```

## Critical Rules

### No emoji in Cairo
`cairo.Context.show_text()` cannot render emoji — they show as squares.
- All UI icons must be Cairo vector shapes (see `widgets/icons.py`)
- All text that might contain non-ASCII must use `PangoCairo.show_layout()`

### Icon loading priority (apps)
1. `icon_path` from config.json (direct file path, highest priority)
2. GTK icon theme lookup by name
3. Filesystem fallback paths
4. Colored circle with initial letter (last resort)

### Known icon paths
- VSCode: `/usr/share/pixmaps/vscode.png`
- WebStorm: `~/.local/share/icons/hicolor/scalable/apps/jetbrains-webstorm-75ff27a5-95d3-4d42-a65b-558f0117f3d0.svg`
- Teams: `~/.local/share/icons/hicolor/48x48/apps/chrome-ompifgpmddkgmclendfeacglnodjjndh-Default.png`

### Cairo vector icons
All system/toggle/music icons are drawn programmatically in `widgets/icons.py`:
`draw_icon(cr, icon_name, cx, cy, size, color)` — centralized function.
Icons: `power`, `restart`, `lock`, `logout`, `moon`, `speaker`, `wifi`, `bluetooth`,
       `play`, `pause`, `prev`, `next`, `search`, `folder`, `home`

### Config
- Never hardcode user preferences in Python files
- All user-editable values live in `config.json`
- `widgets/config.py` exposes a single `CFG` dict loaded at startup

## Running
```bash
python3 widget.py
```

## Dependencies
- Python 3, PyGObject (GTK3, Gdk, Pango, PangoCairo, GdkPixbuf), pycairo
- Optional: `requests` (weather), `playerctl` (music)
- System: `nmcli`, `bluetoothctl`, `redshift`, `pactl`, `xdg-open`
