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
def tools_factory(tmp_path):
    """Create tools instance with temp screenshot dir."""
    import config

    config.SCREENSHOT_DIR = str(tmp_path / "screenshots")
    manager = BrowserManager()
    t = PlaywrightTools(manager)
    return t


@pytest.mark.asyncio
async def test_navigate_returns_title(tools_factory):
    """Navigate should return page title and status."""
    tools = tools_factory
    try:
        result = await tools.navigate("https://example.com")
        assert result["success"] is True
        assert "Example Domain" in result["title"]
        assert result["url"] == "https://example.com/"
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_screenshot_saves_to_disk(tools_factory, tmp_path):
    """Screenshot should save PNG to disk and return path."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.screenshot()
        assert result["success"] is True
        assert result["path"].endswith(".png")
        assert Path(result["path"]).exists()
        assert Path(result["path"]).stat().st_size > 0
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_screenshot_custom_path(tools_factory, tmp_path):
    """Screenshot with custom path should save there."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        custom_path = str(tmp_path / "custom.png")
        result = await tools.screenshot(path=custom_path)
        assert result["path"] == custom_path
        assert Path(custom_path).exists()
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_snapshot_returns_text(tools_factory):
    """Snapshot should return accessibility tree as text."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.snapshot()
        assert result["success"] is True
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_snapshot_respects_max_lines(tools_factory):
    """Snapshot should cap output at max_lines."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.snapshot(max_lines=5)
        lines = result["content"].strip().split("\n")
        assert len(lines) <= 6  # 5 lines + possible truncation message
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_evaluate_returns_result(tools_factory):
    """Evaluate should run JS and return result."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.evaluate("document.title")
        assert result["success"] is True
        assert "Example Domain" in str(result["value"])
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_evaluate_truncates_long_result(tools_factory):
    """Evaluate should truncate results over 2000 chars."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.evaluate("'x'.repeat(5000)")
        assert result["success"] is True
        assert len(str(result["value"])) <= 2100  # small buffer for truncation message
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_click_nonexistent_element(tools_factory):
    """Clicking a missing element should return error."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.click("#nonexistent-element-xyz")
        assert result["success"] is False
        assert "error" in result
    finally:
        await tools.manager.close()


@pytest.mark.asyncio
async def test_close_returns_confirmation(tools_factory):
    """Close should return success confirmation."""
    tools = tools_factory
    try:
        await tools.navigate("https://example.com")
        result = await tools.close()
        assert result["success"] is True
    finally:
        # close() already called in the test, but the fixture needs cleanup
        # Double close is safe (idempotent)
        await tools.manager.close()
