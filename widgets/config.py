"""Load and expose config.json as a module-level dict."""

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

with open(_CONFIG_PATH, "r") as f:
    CFG = json.load(f)

# Expand ~ in paths
CFG["profile_image"] = os.path.expanduser(CFG["profile_image"])
for app in CFG["apps"]:
    if app.get("icon_path"):
        app["icon_path"] = os.path.expanduser(app["icon_path"])
for entry in CFG["files"]:
    entry["path"] = os.path.expanduser(entry["path"])

# Color shortcuts
COLORS = CFG["colors"]
BG     = tuple(COLORS["bg"])
CARD   = tuple(COLORS["card"])
CARD2  = tuple(COLORS["card2"])
BORDER = tuple(COLORS["border"])
PINK   = tuple(COLORS["pink"])
CYAN   = tuple(COLORS["cyan"])
WHITE  = tuple(COLORS["white"])
GREY   = tuple(COLORS["grey"])
DIM    = tuple(COLORS["dim"])
RED    = tuple(COLORS["red"])
GREEN  = tuple(COLORS["green"])
ORANGE = tuple(COLORS["orange"])
PURPLE = tuple(COLORS["purple"])
