#!/usr/bin/env python3
"""Tests for monitoring discovery module."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from services.monitoring.discovery import (
    discover_cron_jobs,
    parse_cron_schedule,
    calculate_expected_interval_minutes,
)


def test_parse_cron_schedule_hourly():
    """Hourly cron should be parsed correctly."""
    result = parse_cron_schedule("0 * * * *")
    assert result["frequency"] == "hourly"


def test_parse_cron_schedule_daily():
    """Daily cron should be parsed correctly."""
    result = parse_cron_schedule("0 0 * * *")
    assert result["frequency"] == "daily"


def test_parse_cron_schedule_every_5_minutes():
    """Every 5 minutes should be parsed correctly."""
    result = parse_cron_schedule("*/5 * * * *")
    assert result["frequency"] == "every_5_minutes"


def test_calculate_expected_interval_hourly():
    """Hourly job should expect 60 minute interval."""
    minutes = calculate_expected_interval_minutes("0 * * * *")
    assert minutes == 60


def test_calculate_expected_interval_daily():
    """Daily job should expect 1440 minute interval."""
    minutes = calculate_expected_interval_minutes("0 0 * * *")
    assert minutes == 1440


def test_calculate_expected_interval_every_5_minutes():
    """Every 5 min job should expect 5 minute interval."""
    minutes = calculate_expected_interval_minutes("*/5 * * * *")
    assert minutes == 5
