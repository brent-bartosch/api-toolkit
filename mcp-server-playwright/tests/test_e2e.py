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

from browser_manager import BrowserManager
from tools import PlaywrightTools


@pytest.fixture
def tools_factory(tmp_path):
    """Create tools instance with temp screenshot dir."""
    import config

    config.SCREENSHOT_DIR = str(tmp_path / "screenshots")
    manager = BrowserManager()
    t = PlaywrightTools(manager)
    return t


@pytest.mark.asyncio
async def test_full_workflow(tools_factory, tmp_path):
    """Test the complete navigate -> screenshot -> snapshot -> evaluate -> click -> screenshot -> close flow."""
    tools = tools_factory
    try:
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

        # 5. Get the actual link text to ensure we click the right element
        link_text = await tools.evaluate("document.querySelector('a').textContent")
        assert link_text["success"] is True
        actual_text = str(link_text["value"]).strip()

        # 6. Click the link using the actual text
        click = await tools.click(f"text={actual_text}")
        assert click["success"] is True
        assert "iana.org" in click["url"]

        # 7. Screenshot after navigation
        shot2 = await tools.screenshot()
        assert shot2["success"] is True
        assert shot2["path"] != shot["path"]  # Different filename

        # 8. Close
        close = await tools.close()
        assert close["success"] is True

    finally:
        await tools.manager.close()
