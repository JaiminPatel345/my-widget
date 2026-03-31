#!/bin/bash
# Auto-start desktop widget on login
# Run once: bash autostart.sh

WIDGET_PATH="$(realpath widget.py)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/desktop-widget.desktop"

mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Desktop Widget
Exec=python3 $WIDGET_PATH
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Glassmorphism desktop widget
EOF

echo "✅ Autostart entry created at: $DESKTOP_FILE"
echo "   Widget will launch automatically on next login."
