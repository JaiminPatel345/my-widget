# my-widget

A Python3 + GTK3 glassmorphism desktop widget for Ubuntu Linux.

## Features

| Section | Details |
|---|---|
| 🕐 Clock / Calendar | Live HH:MM:SS clock, full date, mini monthly calendar |
| 👤 Profile / Weather | Avatar, username, live weather from wttr.in, uptime badge |
| 🎵 Music Control | playerctl / MPRIS integration, spinning vinyl disc, controls |
| 🚀 App Launcher | Icon grid (Chrome, Brave, Discord, YouTube, Calculator, Files) |
| 🔘 Quick Toggles | WiFi · Bluetooth · Night Mode · Power (shutdown/restart/logout) |

Visual style: **glassmorphism** — frosted dark panels, cyan (#00d4ff) accent, animated aurora background, no titlebar, pinned to desktop.

---

## Requirements

- Ubuntu 20.04+ (or any GNOME / X11 desktop)
- Python 3.8+

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/JaiminPatel345/my-widget.git
cd my-widget

# 2. Install dependencies
chmod +x install.sh
./install.sh
```

**Recommended fonts** (for best appearance):

```bash
# JetBrains Mono (clock digits)
sudo apt install fonts-jetbrains-mono

# Outfit (headings) — download from https://fonts.google.com/specimen/Outfit
# then copy the .ttf files to ~/.fonts/ and run: fc-cache -fv
```

---

## Configuration

Edit the top of `widget.py`:

```python
USERNAME           = "YourName"          # display name (default: $USER)
PROFILE_IMAGE_PATH = "~/Pictures/profile.jpg"  # avatar image
CITY               = "London"            # city for weather (default: auto-detect)
```

---

## Running

```bash
python3 widget.py
```

---

## Autostart on login

```bash
# Copy the autostart entry — edit the Exec path to match your install location
cp autostart.desktop ~/.config/autostart/desktop-widget.desktop
```

Then edit `~/.config/autostart/desktop-widget.desktop` and update the `Exec=` line to the full path of `widget.py` on your system.

---

## Files

| File | Purpose |
|---|---|
| `widget.py` | Main widget (single Python file) |
| `install.sh` | Dependency installer |
| `autostart.desktop` | GNOME autostart entry |
| `README.md` | This file |

---

## Dependencies

| Package | Purpose |
|---|---|
| `python3-gi`, `python3-gi-cairo`, `gir1.2-gtk-3.0` | GTK3 Python bindings |
| `playerctl` | Music / MPRIS control |
| `redshift` | Night mode (color temperature) |
| `network-manager` (`nmcli`) | WiFi toggle |
| `bluez` (`bluetoothctl`) | Bluetooth toggle |
| `requests` (pip) | Weather API calls |

---

## Troubleshooting

- **Transparent background not working** — ensure your compositor supports RGBA visuals (Compiz / Mutter / Picom).
- **Weather shows "unavailable"** — check internet access and that `requests` is installed (`pip3 install requests`).
- **Music section shows "Nothing playing"** — install `playerctl` and start a media player that exposes MPRIS (most desktop media players do, browser audio may need a browser extension).
- **Icons missing** — install the relevant app (Chrome/Brave/Discord) so its `.desktop` entry and icon are registered in the system icon theme.
