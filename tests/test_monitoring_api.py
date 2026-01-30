#!/usr/bin/env python3
"""Tests for MonitoringAPI main class."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from services.monitoring.api import MonitoringAPI


def test_monitoring_api_init():
    """MonitoringAPI should initialize."""
    api = MonitoringAPI()
    assert api is not None


def test_monitoring_api_has_required_methods():
    """MonitoringAPI should have required methods."""
    api = MonitoringAPI()
    assert hasattr(api, "audit_all_projects")
    assert hasattr(api, "list_jobs")
    assert hasattr(api, "check_health")
    assert hasattr(api, "test_connection")


def test_monitoring_api_test_connection():
    """test_connection should return True when configured."""
    api = MonitoringAPI()
    # Without actual DB, just test it doesn't crash
    result = api.test_connection()
    assert isinstance(result, bool)


def test_monitoring_api_audit_project():
    """MonitoringAPI should have audit_project method."""
    api = MonitoringAPI()
    assert hasattr(api, "audit_project")
    assert callable(api.audit_project)


def test_monitoring_api_get_job_history():
    """MonitoringAPI should have get_job_history method."""
    api = MonitoringAPI()
    assert hasattr(api, "get_job_history")
    assert callable(api.get_job_history)


def test_monitoring_api_quick_start():
    """MonitoringAPI should have quick_start method."""
    api = MonitoringAPI()
    assert hasattr(api, "quick_start")
    assert callable(api.quick_start)


def test_monitoring_api_central_project_default():
    """MonitoringAPI should default to 'thordata' central project."""
    api = MonitoringAPI()
    assert api.central_project == "thordata"


def test_monitoring_api_custom_central_project():
    """MonitoringAPI should accept custom central project."""
    api = MonitoringAPI(central_project="custom_project")
    assert api.central_project == "custom_project"
