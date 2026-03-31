#!/usr/bin/env bash
# install.sh — Install dependencies for the desktop widget
set -e

echo "==> Updating package list…"
sudo apt-get update -y

echo "==> Installing system packages…"
sudo apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    playerctl \
    redshift \
    network-manager \
    bluetooth \
    bluez \
    curl

echo "==> Installing Python packages…"
pip3 install --user requests

echo ""
echo "==> All dependencies installed."
echo ""
echo "Optional: install JetBrains Mono and Outfit fonts for best appearance:"
echo "  sudo apt-get install fonts-jetbrains-mono"
echo "  # Outfit: download from https://fonts.google.com/specimen/Outfit"
echo ""
echo "Run the widget with:  python3 widget.py"
