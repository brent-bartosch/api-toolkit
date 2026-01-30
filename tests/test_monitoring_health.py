#!/usr/bin/env python3
"""Tests for monitoring health check module."""
import pytest
from datetime import datetime, timedelta
from services.monitoring.health_check import (
    check_job_status,
    is_job_overdue,
    JobStatus,
)


def test_check_job_status_success():
    """Successful run should return success status."""
    status = check_job_status(
        last_status="succeeded",
        last_run=datetime.now() - timedelta(minutes=30),
        expected_interval=60,
    )
    assert status == JobStatus.SUCCESS


def test_check_job_status_failed():
    """Failed run should return failed status."""
    status = check_job_status(
        last_status="failed",
        last_run=datetime.now() - timedelta(minutes=5),
        expected_interval=60,
    )
    assert status == JobStatus.FAILED


def test_check_job_status_missed():
    """Job that hasn't run should return missed status."""
    status = check_job_status(
        last_status="succeeded",
        last_run=datetime.now() - timedelta(minutes=120),
        expected_interval=60,  # Should have run within 60 mins
    )
    assert status == JobStatus.MISSED


def test_is_job_overdue_true():
    """Job past its interval should be overdue."""
    result = is_job_overdue(
        last_run=datetime.now() - timedelta(minutes=100),
        expected_interval_minutes=60,
        buffer_percent=50,  # 60 * 1.5 = 90 minutes
    )
    assert result is True


def test_is_job_overdue_false():
    """Job within interval should not be overdue."""
    result = is_job_overdue(
        last_run=datetime.now() - timedelta(minutes=50),
        expected_interval_minutes=60,
        buffer_percent=50,
    )
    assert result is False
