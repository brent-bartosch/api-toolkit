#!/usr/bin/env python3
"""Configuration defaults for the Playwright MCP server."""

import os
from pathlib import Path

# Browser settings
BROWSER_TYPE = "chromium"
HEADLESS = True
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
DEFAULT_TIMEOUT_MS = 30000

# Screenshot settings
SCREENSHOT_DIR = os.getenv(
    "PLAYWRIGHT_SCREENSHOT_DIR", os.path.join(os.getcwd(), ".playwright", "screenshots")
)
SCREENSHOT_CLEANUP_HOURS = 24

# Snapshot settings
MAX_SNAPSHOT_LINES = 200

# Evaluate settings
MAX_EVAL_RESULT_CHARS = 2000

# Navigation settings
WAIT_UNTIL = "networkidle"
