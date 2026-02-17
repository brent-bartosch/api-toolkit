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
