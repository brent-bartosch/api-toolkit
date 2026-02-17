#!/usr/bin/env python3
"""
Playwright tool implementations.
Each method maps 1:1 to an MCP tool exposed by the server.
"""

from datetime import datetime
from pathlib import Path

import config
from browser_manager import BrowserManager


class PlaywrightTools:
    """Implements the 8 browser tools."""

    def __init__(self, manager: BrowserManager):
        self.manager = manager

    async def navigate(self, url: str) -> dict:
        """Navigate to a URL. Waits for network idle."""
        try:
            page = await self.manager.get_page()
            response = await page.goto(url, wait_until=config.WAIT_UNTIL)
            status = response.status if response else None
            title = await page.title()
            return {
                "success": True,
                "title": title,
                "url": page.url,
                "status": status,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(
        self, path: str | None = None, full_page: bool = False
    ) -> dict:
        """Take a screenshot and save to disk."""
        try:
            page = await self.manager.get_page()
            if path is None:
                screenshot_dir = self.manager.ensure_screenshot_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(screenshot_dir / f"screenshot_{timestamp}.png")
            else:
                Path(path).parent.mkdir(parents=True, exist_ok=True)

            await page.screenshot(path=path, full_page=full_page)
            self.manager.cleanup_old_screenshots()
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str) -> dict:
        """Click an element by CSS or text selector."""
        try:
            page = await self.manager.get_page()
            await page.click(selector, timeout=config.DEFAULT_TIMEOUT_MS)
            await page.wait_for_load_state("networkidle")
            title = await page.title()
            return {
                "success": True,
                "url": page.url,
                "title": title,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str) -> dict:
        """Type text into an input element."""
        try:
            page = await self.manager.get_page()
            await page.fill(selector, text)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def select(self, selector: str, value: str) -> dict:
        """Select an option from a dropdown."""
        try:
            page = await self.manager.get_page()
            await page.select_option(selector, value)
            return {"success": True, "selector": selector, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def snapshot(self, max_lines: int | None = None) -> dict:
        """Get the page's accessibility tree, trimmed to max_lines."""
        if max_lines is None:
            max_lines = config.MAX_SNAPSHOT_LINES
        try:
            page = await self.manager.get_page()
            snap = await page.accessibility.snapshot()
            if snap is None:
                return {"success": True, "content": "(empty page)"}

            lines = _format_a11y_tree(snap)
            trimmed = lines[:max_lines]
            content = "\n".join(trimmed)
            if len(lines) > max_lines:
                content += f"\n... ({len(lines) - max_lines} more lines truncated)"
            return {"success": True, "content": content, "total_lines": len(lines)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate(self, script: str) -> dict:
        """Execute JavaScript on the page and return the result."""
        try:
            page = await self.manager.get_page()
            result = await page.evaluate(script)
            result_str = str(result)
            if len(result_str) > config.MAX_EVAL_RESULT_CHARS:
                result_str = (
                    result_str[: config.MAX_EVAL_RESULT_CHARS] + "... (truncated)"
                )
                return {"success": True, "value": result_str, "truncated": True}
            return {"success": True, "value": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self) -> dict:
        """Close the browser session."""
        try:
            await self.manager.close()
            return {"success": True, "message": "Browser closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def _format_a11y_tree(node: dict, indent: int = 0) -> list[str]:
    """Format an accessibility tree node into readable lines."""
    lines = []
    prefix = "  " * indent
    role = node.get("role", "")
    name = node.get("name", "")
    value = node.get("value", "")

    parts = [role]
    if name:
        parts.append(f'"{name}"')
    if value:
        parts.append(f"value={value}")
    lines.append(f"{prefix}{' '.join(parts)}")

    for child in node.get("children", []):
        lines.extend(_format_a11y_tree(child, indent + 1))
    return lines
