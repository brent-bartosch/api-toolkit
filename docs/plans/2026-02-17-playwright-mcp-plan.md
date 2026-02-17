# Playwright Curated MCP Proxy -- Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a token-efficient MCP server that gives Claude Code visual + interactive access to frontends via Playwright, using ~2K tokens instead of the stock 20K+.

**Architecture:** A standalone MCP server at `mcp-server-playwright/` wrapping Playwright directly. Exposes 8 tools via MCP protocol. Screenshots saved to disk (not inline). Browser managed as a lazy singleton.

**Tech Stack:** Python 3.11+, `playwright` (already installed v1.55), `mcp` Python SDK (>=0.9.0), asyncio

**Design doc:** `docs/plans/2026-02-17-playwright-mcp-design.md`

---

### Task 1: Project Scaffold & Config

**Files:**
- Create: `mcp-server-playwright/config.py`
- Create: `mcp-server-playwright/requirements.txt`
- Create: `mcp-server-playwright/__init__.py`

**Step 1: Create the directory**

```bash
mkdir -p /Users/brentbartosch/Development/api-toolkit/mcp-server-playwright
```

**Step 2: Write `requirements.txt`**

Create `mcp-server-playwright/requirements.txt`:
```
mcp>=0.9.0
playwright>=1.40.0
```

**Step 3: Write `config.py`**

Create `mcp-server-playwright/config.py`:
```python
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
    "PLAYWRIGHT_SCREENSHOT_DIR",
    os.path.join(os.getcwd(), ".playwright", "screenshots")
)
SCREENSHOT_CLEANUP_HOURS = 24

# Snapshot settings
MAX_SNAPSHOT_LINES = 200

# Evaluate settings
MAX_EVAL_RESULT_CHARS = 2000

# Navigation settings
WAIT_UNTIL = "networkidle"
```

**Step 4: Write empty `__init__.py`**

Create `mcp-server-playwright/__init__.py`:
```python
```

**Step 5: Commit**

```bash
git add mcp-server-playwright/
git commit -m "feat(playwright-mcp): scaffold project with config"
```

---

### Task 2: Browser Manager

**Files:**
- Create: `mcp-server-playwright/browser_manager.py`
- Create: `mcp-server-playwright/tests/test_browser_manager.py`

**Step 1: Write the failing test**

Create `mcp-server-playwright/tests/__init__.py` (empty) and `mcp-server-playwright/tests/test_browser_manager.py`:
```python
#!/usr/bin/env python3
"""Tests for browser_manager.py"""

import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_manager import BrowserManager


@pytest.fixture
def manager():
    return BrowserManager()


def test_manager_starts_without_browser(manager):
    """Browser should not launch until first use."""
    assert manager._browser is None
    assert manager._page is None


@pytest.mark.asyncio
async def test_get_page_launches_browser(manager):
    """First call to get_page should launch browser."""
    try:
        page = await manager.get_page()
        assert page is not None
        assert manager._browser is not None
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_get_page_reuses_browser(manager):
    """Subsequent calls should return the same page."""
    try:
        page1 = await manager.get_page()
        page2 = await manager.get_page()
        assert page1 is page2
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_close_cleans_up(manager):
    """Close should shut down browser and reset state."""
    await manager.get_page()
    await manager.close()
    assert manager._browser is None
    assert manager._page is None


@pytest.mark.asyncio
async def test_close_idempotent(manager):
    """Closing when already closed should not error."""
    await manager.close()  # Should not raise
    await manager.close()  # Should not raise
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/brentbartosch/Development/api-toolkit && python -m pytest mcp-server-playwright/tests/test_browser_manager.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'browser_manager'`

**Step 3: Write `browser_manager.py`**

Create `mcp-server-playwright/browser_manager.py`:
```python
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
        self._browser = await self._playwright.chromium.launch(
            headless=config.HEADLESS
        )
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/brentbartosch/Development/api-toolkit && python -m pytest mcp-server-playwright/tests/test_browser_manager.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add mcp-server-playwright/browser_manager.py mcp-server-playwright/tests/
git commit -m "feat(playwright-mcp): add browser manager with lazy launch"
```

---

### Task 3: Tool Implementations

**Files:**
- Create: `mcp-server-playwright/tools.py`
- Create: `mcp-server-playwright/tests/test_tools.py`

**Step 1: Write failing tests**

Create `mcp-server-playwright/tests/test_tools.py`:
```python
#!/usr/bin/env python3
"""Tests for tool implementations."""

import asyncio
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_manager import BrowserManager
from tools import PlaywrightTools


@pytest.fixture
async def tools(tmp_path):
    """Create tools instance with temp screenshot dir."""
    import config
    config.SCREENSHOT_DIR = str(tmp_path / "screenshots")
    manager = BrowserManager()
    t = PlaywrightTools(manager)
    yield t
    await manager.close()


@pytest.mark.asyncio
async def test_navigate_returns_title(tools):
    """Navigate should return page title and status."""
    result = await tools.navigate("https://example.com")
    assert result["success"] is True
    assert "Example Domain" in result["title"]
    assert result["url"] == "https://example.com/"


@pytest.mark.asyncio
async def test_screenshot_saves_to_disk(tools, tmp_path):
    """Screenshot should save PNG to disk and return path."""
    await tools.navigate("https://example.com")
    result = await tools.screenshot()
    assert result["success"] is True
    assert result["path"].endswith(".png")
    assert Path(result["path"]).exists()
    assert Path(result["path"]).stat().st_size > 0


@pytest.mark.asyncio
async def test_screenshot_custom_path(tools, tmp_path):
    """Screenshot with custom path should save there."""
    await tools.navigate("https://example.com")
    custom_path = str(tmp_path / "custom.png")
    result = await tools.screenshot(path=custom_path)
    assert result["path"] == custom_path
    assert Path(custom_path).exists()


@pytest.mark.asyncio
async def test_snapshot_returns_text(tools):
    """Snapshot should return accessibility tree as text."""
    await tools.navigate("https://example.com")
    result = await tools.snapshot()
    assert result["success"] is True
    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0


@pytest.mark.asyncio
async def test_snapshot_respects_max_lines(tools):
    """Snapshot should cap output at max_lines."""
    await tools.navigate("https://example.com")
    result = await tools.snapshot(max_lines=5)
    lines = result["content"].strip().split("\n")
    assert len(lines) <= 5


@pytest.mark.asyncio
async def test_evaluate_returns_result(tools):
    """Evaluate should run JS and return result."""
    await tools.navigate("https://example.com")
    result = await tools.evaluate("document.title")
    assert result["success"] is True
    assert "Example Domain" in str(result["value"])


@pytest.mark.asyncio
async def test_evaluate_truncates_long_result(tools):
    """Evaluate should truncate results over 2000 chars."""
    await tools.navigate("https://example.com")
    result = await tools.evaluate("'x'.repeat(5000)")
    assert result["success"] is True
    assert len(str(result["value"])) <= 2100  # small buffer for truncation message


@pytest.mark.asyncio
async def test_click_nonexistent_element(tools):
    """Clicking a missing element should return error."""
    await tools.navigate("https://example.com")
    result = await tools.click("#nonexistent-element-xyz")
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_close_returns_confirmation(tools):
    """Close should return success confirmation."""
    await tools.navigate("https://example.com")
    result = await tools.close()
    assert result["success"] is True
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/brentbartosch/Development/api-toolkit && python -m pytest mcp-server-playwright/tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools'`

**Step 3: Write `tools.py`**

Create `mcp-server-playwright/tools.py`:
```python
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
            snapshot = await page.accessibility.snapshot()
            if snapshot is None:
                return {"success": True, "content": "(empty page)"}

            lines = _format_a11y_tree(snapshot)
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
                    result_str[: config.MAX_EVAL_RESULT_CHARS]
                    + "... (truncated)"
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/brentbartosch/Development/api-toolkit && python -m pytest mcp-server-playwright/tests/test_tools.py -v`
Expected: All 10 tests PASS (some may be slow due to browser launch + network)

**Step 5: Commit**

```bash
git add mcp-server-playwright/tools.py mcp-server-playwright/tests/test_tools.py
git commit -m "feat(playwright-mcp): implement 8 browser tools"
```

---

### Task 4: MCP Server

**Files:**
- Create: `mcp-server-playwright/server.py`

**Step 1: Write `server.py`**

Create `mcp-server-playwright/server.py`:
```python
#!/usr/bin/env python3
"""
Playwright Curated MCP Server
Token-efficient MCP server exposing 8 Playwright tools (~2K tokens).
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from browser_manager import BrowserManager
from tools import PlaywrightTools


class PlaywrightMCPServer:
    """Lightweight MCP server for Playwright browser automation."""

    def __init__(self):
        self.server = Server("playwright")
        self.manager = BrowserManager()
        self.tools = PlaywrightTools(self.manager)
        self._setup_handlers()

    def _setup_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="browser_navigate",
                    description="Navigate to a URL. Returns page title and status.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to",
                            }
                        },
                        "required": ["url"],
                    },
                ),
                Tool(
                    name="browser_screenshot",
                    description="Take screenshot, save to disk. Returns file path (use Read tool to view).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Optional file path. Auto-generated if omitted.",
                            },
                            "full_page": {
                                "type": "boolean",
                                "description": "Capture full scrollable page (default false)",
                                "default": False,
                            },
                        },
                    },
                ),
                Tool(
                    name="browser_click",
                    description="Click an element. Supports CSS selectors and text= selectors.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": 'CSS or text selector (e.g., "#btn", "text=Sign In")',
                            }
                        },
                        "required": ["selector"],
                    },
                ),
                Tool(
                    name="browser_type",
                    description="Type text into an input field.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the input",
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type",
                            },
                        },
                        "required": ["selector", "text"],
                    },
                ),
                Tool(
                    name="browser_select",
                    description="Select a dropdown option by value.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the select element",
                            },
                            "value": {
                                "type": "string",
                                "description": "Option value to select",
                            },
                        },
                        "required": ["selector", "value"],
                    },
                ),
                Tool(
                    name="browser_snapshot",
                    description="Get page accessibility tree as text. Good for understanding page structure without a screenshot.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_lines": {
                                "type": "integer",
                                "description": "Max lines to return (default 200)",
                                "default": 200,
                            }
                        },
                    },
                ),
                Tool(
                    name="browser_evaluate",
                    description="Run JavaScript on the page. Returns result (truncated to 2000 chars).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "JavaScript to evaluate",
                            }
                        },
                        "required": ["script"],
                    },
                ),
                Tool(
                    name="browser_close",
                    description="Close the browser session.",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            dispatch = {
                "browser_navigate": lambda args: self.tools.navigate(args["url"]),
                "browser_screenshot": lambda args: self.tools.screenshot(
                    path=args.get("path"), full_page=args.get("full_page", False)
                ),
                "browser_click": lambda args: self.tools.click(args["selector"]),
                "browser_type": lambda args: self.tools.type_text(
                    args["selector"], args["text"]
                ),
                "browser_select": lambda args: self.tools.select(
                    args["selector"], args["value"]
                ),
                "browser_snapshot": lambda args: self.tools.snapshot(
                    max_lines=args.get("max_lines")
                ),
                "browser_evaluate": lambda args: self.tools.evaluate(args["script"]),
                "browser_close": lambda args: self.tools.close(),
            }

            if name not in dispatch:
                return [
                    TextContent(type="text", text=f"Unknown tool: {name}")
                ]

            try:
                result = await dispatch[name](arguments)
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"success": False, "error": str(e)}),
                    )
                ]

    async def run(self):
        """Run the MCP server via stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def cleanup(self):
        """Clean up browser on shutdown."""
        await self.manager.close()


def main():
    server = PlaywrightMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        asyncio.run(server.cleanup())


if __name__ == "__main__":
    main()
```

**Step 2: Verify server starts without errors**

Run: `cd /Users/brentbartosch/Development/api-toolkit/mcp-server-playwright && timeout 3 python server.py 2>&1; echo "Exit: $?"`
Expected: Server starts and waits for MCP protocol input. Should exit cleanly on timeout/EOF without errors.

**Step 3: Commit**

```bash
git add mcp-server-playwright/server.py
git commit -m "feat(playwright-mcp): add MCP server with 8 tools"
```

---

### Task 5: Installation & Documentation

**Files:**
- Create: `mcp-server-playwright/INSTALLATION.md`
- Create: `mcp-server-playwright/README.md`

**Step 1: Write `INSTALLATION.md`**

Create `mcp-server-playwright/INSTALLATION.md`:
```markdown
# Playwright MCP Server -- Installation

## Prerequisites

```bash
pip install playwright mcp
playwright install chromium
```

## Claude Code Setup

Add to your project's `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "python",
      "args": ["/Users/brentbartosch/Development/api-toolkit/mcp-server-playwright/server.py"],
      "env": {}
    }
  }
}
```

Or add globally at `~/.claude.json`.

## Verify

Restart Claude Code. You should see 8 `browser_*` tools available.

## Screenshot Directory

Screenshots are saved to `.playwright/screenshots/` in your working directory.
Add to `.gitignore`:

```
.playwright/
```
```

**Step 2: Write `README.md`**

Create `mcp-server-playwright/README.md`:
```markdown
# Playwright Curated MCP Server

Token-efficient Playwright MCP server (~2K tokens) for visual + interactive frontend development.

## Tools (8)

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Load a URL |
| `browser_screenshot` | Capture page to disk (returns file path) |
| `browser_click` | Click element (CSS/text selector) |
| `browser_type` | Type into input field |
| `browser_select` | Select dropdown option |
| `browser_snapshot` | Get accessibility tree as text |
| `browser_evaluate` | Run JavaScript |
| `browser_close` | Close browser session |

## Token Comparison

| Approach | Tool Schema Tokens |
|----------|--------------------|
| Stock Playwright MCP (34 tools) | ~20,000 |
| **This server (8 tools)** | **~2,000** |

## Usage

Navigate to a page, take a screenshot, then use Read tool to view it:

1. `browser_navigate` with your staging URL
2. `browser_screenshot` to capture the page
3. View the screenshot file with Read tool
4. `browser_click` / `browser_type` to interact
5. `browser_screenshot` again to verify changes

Screenshots are saved to `.playwright/screenshots/` and auto-cleaned after 24 hours.

## Setup

See `INSTALLATION.md`.
```

**Step 3: Commit**

```bash
git add mcp-server-playwright/INSTALLATION.md mcp-server-playwright/README.md
git commit -m "docs(playwright-mcp): add installation and usage docs"
```

---

### Task 6: Slash Command

**Files:**
- Create: `.claude/commands/playwright.md`

**Step 1: Write slash command**

Create `/Users/brentbartosch/Development/api-toolkit/.claude/commands/playwright.md`:
```markdown
---
description: Load Playwright MCP context for browser automation
---

# Playwright MCP -- Quick Reference

8 tools available via MCP for visual + interactive frontend work:

| Tool | Example |
|------|---------|
| `browser_navigate` | `{"url": "https://staging.example.com"}` |
| `browser_screenshot` | `{}` or `{"full_page": true}` |
| `browser_click` | `{"selector": "#submit-btn"}` or `{"selector": "text=Sign In"}` |
| `browser_type` | `{"selector": "input[name='email']", "text": "test@example.com"}` |
| `browser_select` | `{"selector": "#country", "value": "US"}` |
| `browser_snapshot` | `{"max_lines": 100}` |
| `browser_evaluate` | `{"script": "document.querySelectorAll('.item').length"}` |
| `browser_close` | `{}` |

**Workflow**: Navigate -> Screenshot -> View with Read tool -> Interact -> Screenshot again

**Screenshots**: Saved to `.playwright/screenshots/`, auto-cleaned after 24h. Use Read tool to view.

**Selectors**: CSS (`#id`, `.class`, `input[name='x']`) or text (`text=Click Me`).
```

**Step 2: Commit**

```bash
git add .claude/commands/playwright.md
git commit -m "feat(playwright-mcp): add /playwright slash command"
```

---

### Task 7: Integration Test (End-to-End)

**Files:**
- Create: `mcp-server-playwright/tests/test_e2e.py`

**Step 1: Write E2E test**

Create `mcp-server-playwright/tests/test_e2e.py`:
```python
#!/usr/bin/env python3
"""
End-to-end test: navigate, screenshot, interact, verify.
Uses example.com as a stable test target.
"""

import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from browser_manager import BrowserManager
from tools import PlaywrightTools


@pytest.fixture
async def tools(tmp_path):
    config.SCREENSHOT_DIR = str(tmp_path / "screenshots")
    manager = BrowserManager()
    t = PlaywrightTools(manager)
    yield t
    await manager.close()


@pytest.mark.asyncio
async def test_full_workflow(tools, tmp_path):
    """Test the complete navigate -> screenshot -> snapshot -> evaluate -> close flow."""

    # 1. Navigate
    nav = await tools.navigate("https://example.com")
    assert nav["success"] is True
    assert "Example Domain" in nav["title"]

    # 2. Screenshot
    shot = await tools.screenshot()
    assert shot["success"] is True
    assert Path(shot["path"]).exists()
    assert Path(shot["path"]).stat().st_size > 1000  # Not a blank image

    # 3. Snapshot
    snap = await tools.snapshot(max_lines=50)
    assert snap["success"] is True
    assert len(snap["content"]) > 0

    # 4. Evaluate
    ev = await tools.evaluate("document.querySelector('h1').textContent")
    assert ev["success"] is True
    assert "Example Domain" in str(ev["value"])

    # 5. Click a link
    click = await tools.click("text=More information...")
    assert click["success"] is True
    assert "iana.org" in click["url"]

    # 6. Screenshot after navigation
    shot2 = await tools.screenshot()
    assert shot2["success"] is True
    assert shot2["path"] != shot["path"]  # Different filename

    # 7. Close
    close = await tools.close()
    assert close["success"] is True
```

**Step 2: Run E2E test**

Run: `cd /Users/brentbartosch/Development/api-toolkit && python -m pytest mcp-server-playwright/tests/test_e2e.py -v`
Expected: All assertions PASS

**Step 3: Commit**

```bash
git add mcp-server-playwright/tests/test_e2e.py
git commit -m "test(playwright-mcp): add end-to-end workflow test"
```

---

### Task 8: Register in Claude Code MCP Config

**Step 1: Check current MCP config**

Run: `cat ~/.claude.json 2>/dev/null | python -m json.tool || echo "No global config"`
Also check: `cat /Users/brentbartosch/Development/api-toolkit/.claude/mcp.json 2>/dev/null || echo "No project config"`

**Step 2: Add playwright MCP server to config**

The exact command depends on what exists. Use Claude Code's built-in MCP command:

```bash
claude mcp add playwright -- python /Users/brentbartosch/Development/api-toolkit/mcp-server-playwright/server.py
```

Or manually add to `.claude/mcp.json` if it exists.

**Step 3: Verify tools are available**

Restart Claude Code and confirm the 8 `browser_*` tools appear.

**Step 4: Commit config if changed**

```bash
git add .claude/mcp.json
git commit -m "feat(playwright-mcp): register MCP server in Claude Code config"
```

---

### Task 9: Update Project CLAUDE.md

**Files:**
- Modify: `/Users/brentbartosch/Development/api-toolkit/CLAUDE.md` (add Playwright section)

**Step 1: Add Playwright MCP section to CLAUDE.md**

Add after the existing MCP server sections:

```markdown
### 3. Playwright Curated MCP (~2,000 tokens) - Frontend Visual + Interactive

**Best for**: Iterating on UI design and functionality. Navigate staging/preview URLs, take screenshots, click elements, fill forms.

```bash
# Install: pip install -r mcp-server-playwright/requirements.txt && playwright install chromium
# Configure in .claude/mcp.json (see mcp-server-playwright/INSTALLATION.md)
```

**8 tools:**
- `browser_navigate` - Load a URL
- `browser_screenshot` - Capture page to disk (returns file path for Read tool)
- `browser_click` - Click element (CSS/text selector)
- `browser_type` - Type into input field
- `browser_select` - Select dropdown option
- `browser_snapshot` - Get accessibility tree as text
- `browser_evaluate` - Run JavaScript
- `browser_close` - Close browser session

**See:** `mcp-server-playwright/README.md` | `mcp-server-playwright/INSTALLATION.md`
```

**Step 2: Update slash commands table**

Add to the existing slash commands table:
```markdown
| `/playwright` | Browser automation (8 tools) | ~300 |
```

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Playwright MCP section to CLAUDE.md"
```
