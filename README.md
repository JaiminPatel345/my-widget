# 🖥️ Desktop Widget — Glassmorphism Panel

A fully custom always-on-desktop widget for Ubuntu built with Python3 + GTK3.

## 📦 Contents
```
widget.py      ← Main widget (run this)
setup.sh       ← Install all dependencies
autostart.sh   ← Make it launch at login
README.md      ← This file
```

## 🚀 Quick Start

### 1. Install dependencies
```bash
bash setup.sh
```

### 2. Personalise
Open `widget.py` and edit the top CONFIG section:
```python
USER_NAME   = "Your Name"    # ← your name
CITY        = "New York"     # ← your city for weather
PROFILE_IMG = "~/.config/desktop-widget/profile.jpg"  # ← your photo
```

Copy your profile photo:
```bash
cp /path/to/your/photo.jpg ~/.config/desktop-widget/profile.jpg
```

### 3. Run
```bash
python3 widget.py
```

### 4. Auto-start on login (optional)
```bash
bash autostart.sh
```

---

## 🎛️ Widget Sections

| Section       | Details |
|---------------|---------|
| 👤 Profile    | Your photo, name, live weather |
| 🕐 Clock      | Live HH:MM:SS + seconds arc |
| 📅 Calendar   | Current month, today highlighted |
| 🎵 Music      | Spinning CD disc, YouTube Music link, play/pause toggle |
| 🚀 App Launcher | Chrome, Discord, Brave, YouTube, Calculator — one click |
| 🔘 Toggles   | Wi-Fi, Bluetooth, Night Mode (redshift), Brightness, Power |

---

## 🎨 Customisation

### Add/change apps
Edit the `APPS` list in `widget.py`:
```python
APPS = [
    {"name": "Chrome",  "icon": "🌐", "cmd": "google-chrome"},
    {"name": "Discord", "icon": "💬", "cmd": "discord"},
    # add more here...
]
```

### Change position
By default the widget is **centered** on screen. To move it, edit `widget.py`:
```python
self.move(100, 100)   # x=100px from left, y=100px from top
```

### Change size
```python
WIDGET_W = 650   # width
WIDGET_H = 630   # height
```

---

## 🔧 Troubleshooting

**Widget not transparent?**
Make sure your compositor is running (Compiz, Picom, or GNOME's built-in compositor).

**Weather not loading?**
Check your internet connection. Weather uses `wttr.in` (free, no API key needed).

**Brightness control not working?**
```bash
sudo usermod -aG video $USER
# then log out and back in
```

**Bluetooth toggle not working?**
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```
