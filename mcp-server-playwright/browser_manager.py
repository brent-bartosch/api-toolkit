#!/usr/bin/env python3
"""
Manages Playwright browser lifecycle.
Lazy-launches a single headless browser, reuses it across tool calls.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

import config


class BrowserManager:
    """Singleton-style browser manager with lazy initialization."""

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def get_page(self) -> Page:
        """Get the current page, launching browser if needed."""
        if self._page is None or self._page.is_closed():
            await self._launch()
        return self._page

    async def _launch(self):
        """Launch browser with configured settings."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=config.HEADLESS)
        self._context = await self._browser.new_context(
            viewport={
                "width": config.VIEWPORT_WIDTH,
                "height": config.VIEWPORT_HEIGHT,
            }
        )
        self._context.set_default_timeout(config.DEFAULT_TIMEOUT_MS)
        self._page = await self._context.new_page()

    async def close(self):
        """Close browser and clean up resources."""
        if self._page and not self._page.is_closed():
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def ensure_screenshot_dir(self) -> Path:
        """Create and return the screenshot directory path."""
        screenshot_dir = Path(config.SCREENSHOT_DIR)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        return screenshot_dir

    def cleanup_old_screenshots(self):
        """Delete screenshots older than configured hours."""
        screenshot_dir = Path(config.SCREENSHOT_DIR)
        if not screenshot_dir.exists():
            return
        cutoff = datetime.now() - timedelta(hours=config.SCREENSHOT_CLEANUP_HOURS)
        for f in screenshot_dir.glob("screenshot_*.png"):
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
