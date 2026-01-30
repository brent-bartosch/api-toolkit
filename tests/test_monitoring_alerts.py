#!/usr/bin/env python3
"""Tests for monitoring alerts module."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from services.monitoring.alerts import (
    format_discord_message,
    format_telegram_message,
    AlertSender,
)


def test_format_discord_message_failed():
    """Failed job should format with warning emoji."""
    msg = format_discord_message(
        job_name="sync_leads",
        project="smoothed",
        status="failed",
        error="connection timeout",
    )
    assert "sync_leads" in msg
    assert "smoothed" in msg
    assert "connection timeout" in msg


def test_format_discord_message_missed():
    """Missed job should format with clock emoji."""
    msg = format_discord_message(
        job_name="daily_report",
        project="blingsting",
        status="missed",
    )
    assert "daily_report" in msg
    assert "missed" in msg.lower() or "hasn't run" in msg.lower()


def test_format_telegram_message_critical():
    """Critical alert should have urgent formatting."""
    msg = format_telegram_message(
        job_name="payment_sync",
        project="blingsting",
        status="failed",
        error="database error",
    )
    assert "CRITICAL" in msg or "payment_sync" in msg
    assert "blingsting" in msg


def test_alert_sender_init_with_env():
    """AlertSender should read from environment."""
    with patch.dict(
        "os.environ",
        {
            "DISCORD_WEBHOOK_URL": "https://discord.com/webhook/test",
            "TELEGRAM_BOT_TOKEN": "123:ABC",
            "TELEGRAM_CHAT_ID": "456",
        },
    ):
        sender = AlertSender()
        assert sender.discord_url == "https://discord.com/webhook/test"
        assert sender.telegram_token == "123:ABC"
        assert sender.telegram_chat_id == "456"
