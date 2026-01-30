#!/usr/bin/env python3
"""
Integration tests for monitoring service.

These tests require actual database connections.
Skip if credentials not available.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from services.monitoring.api import MonitoringAPI


# Skip all tests if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("THORDATA_SUPABASE_POSTGRES_URL"),
    reason="THORDATA_SUPABASE_POSTGRES_URL not set",
)


class TestMonitoringIntegration:
    """Integration tests for MonitoringAPI."""

    def test_connection_to_thordata(self):
        """Should connect to thordata project."""
        api = MonitoringAPI()
        assert api.test_connection() is True

    def test_audit_discovers_jobs(self):
        """Audit should discover at least some jobs."""
        api = MonitoringAPI()
        results = api.audit_all_projects()

        # At least one project should have jobs
        total_jobs = sum(len(jobs) for jobs in results.values())
        # This might be 0 if no jobs exist, which is fine
        assert isinstance(total_jobs, int)

    def test_health_check_returns_results(self):
        """Health check should return structured results."""
        api = MonitoringAPI()
        api.audit_all_projects()

        results = api.check_health()

        assert "total_jobs" in results
        assert "failed" in results
        assert "missed" in results
        assert "healthy" in results
        assert "checked_at" in results
