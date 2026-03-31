#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Desktop Widget - One-time Setup Script
#  Run once: bash setup.sh
# ─────────────────────────────────────────────────────────────

set -e

echo "📦 Installing dependencies..."
sudo apt update -qq
sudo apt install -y \
  python3-gi \
  python3-gi-cairo \
  gir1.2-gtk-3.0 \
  gir1.2-gdkpixbuf-2.0 \
  python3-cairo \
  redshift \
  brightnessctl \
  network-manager \
  bluez

echo ""
echo "📁 Creating config directory..."
mkdir -p ~/.config/desktop-widget

echo ""
echo "✅ Setup complete!"
echo ""
echo "─────────────────────────────────────────────────────"
echo "  BEFORE RUNNING — edit widget.py and change:"
echo ""
echo "  USER_NAME = 'Your Name'     ← your name"
echo "  CITY      = 'New York'      ← your city (for weather)"
echo ""
echo "  Profile photo (optional):"
echo "  Copy your photo to:  ~/.config/desktop-widget/profile.jpg"
echo "─────────────────────────────────────────────────────"
echo ""
echo "▶  Run the widget:"
echo "   python3 widget.py"
echo ""
echo "▶  Auto-start on login:"
echo "   bash autostart.sh"
echo ""
